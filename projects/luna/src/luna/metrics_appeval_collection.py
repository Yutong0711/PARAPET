from luna.state_abstraction_utils import AbstractStateExtraction
from luna.probabilistic_abstraction_model import (
    HmmModel,
    DtmcModel,
)
from luna.abstraction_model import RegularGrid
from luna.utils.interfaces import Grid

from sklearn.metrics import pairwise_distances
import numpy as np
import statistics
import random
from sklearn import metrics
from collections import Counter
import torch
from scipy.special import kl_div


class MetricsAppEvalCollections:
    def __init__(
        self,
        abs_args,
        prob_args,
        train_instances=None,
        val_instances=None,
        test_instances=None,
    ):
        result_eval_path = "{}/eval/{}".format(abs_args.result_save_path, abs_args.llm_name) 
        abs_args.result_eval_path = result_eval_path
        self.abstractStateExtraction = AbstractStateExtraction(
            abs_args, train_instances, val_instances, test_instances
        )
        self.dataset = prob_args.dataset

        state_binding_dataset = [
            "truthful_qa",
            "mbpp",
            "humaneval",
            "code_search_net_java",
            "tl_code_sum",
        ]

        if prob_args.model_type == "DTMC":
            self.dtmc_model = DtmcModel(
                prob_args.dataset,
                prob_args.extract_block_idx,
                prob_args.info_type,
                prob_args.cluster_method,
                prob_args.abstract_state,
                prob_args.pca_dim,
                prob_args.test_ratio,
                prob_args.is_attack_success,
                prob_args.grid_history_dependency_num,
                result_eval_path
            )
            self.prob_model = self.dtmc_model
            self.test_abstract_traces = self.dtmc_model.test_traces
            self.val_abstract_traces = self.dtmc_model.val_traces
            self.train_abstract_traces = self.dtmc_model.train_traces

            train_data_points = [{} for _ in range(len(self.train_abstract_traces))]
            for i, one_trace in enumerate(self.train_abstract_traces):
                train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
                train_data_points[i]["label"] = self.dtmc_model.train_groundtruths[i]

            if self.dataset in state_binding_dataset:
                (
                    self.dtmc_state_aucroc,
                    self.dtmc_state_fpr,
                    self.dtmc_state_tpr,
                ) = self.dtmc_model.get_aucroc_by_state_binding()

                self.state_positive_prob_map = self.dtmc_model.construct_dtmc_state_model(
                train_data_points
            )
            else:
                (
                    self.dtmc_transition_aucroc,
                    self.dtmc_transition_fpr,
                    self.dtmc_transition_tpr,
                ) = self.dtmc_model.get_aucroc_by_transition_binding()

        elif prob_args.model_type == "HMM":
            self.hmm_model = HmmModel(
                prob_args.dataset,
                prob_args.extract_block_idx,
                prob_args.info_type,
                prob_args.cluster_method,
                prob_args.abstract_state,
                prob_args.pca_dim,
                prob_args.test_ratio,
                prob_args.hmm_components_num,
                prob_args.iter_num,
                prob_args.is_attack_success,
                prob_args.grid_history_dependency_num,
                result_eval_path
            )

            try:
                if self.dataset in state_binding_dataset:
                    (
                        self.hmm_state_aucroc,
                        self.hmm_state_fpr,
                        self.hmm_state_tpr,
                    ) = self.hmm_model.get_aucroc_by_state_binding()

                    self.state_positive_prob_map = self.hmm_model.state_positive_prob_map
                else:
                    (
                        self.hmm_transition_aucroc,
                        self.hmm_transition_fpr,
                        self.hmm_transition_tpr,
                    ) = self.hmm_model.get_aucroc_by_transition_binding()

                    self.sentence_transition_positive_score_map = self.hmm_model.sentence_transition_positive_score_map 
            except:
                raise ValueError("Cannot Construct HMM Model!")
            
            self.prob_model = self.hmm_model
            self.test_abstract_traces = [
                self.hmm_model.hmm_model.decode([[x] for x in trace])[1].tolist()
                for trace in self.hmm_model.test_traces
            ]
            self.val_abstract_traces = [
                self.hmm_model.hmm_model.decode([[x] for x in trace])[1].tolist()
                for trace in self.hmm_model.val_traces
            ]
            self.train_abstract_traces = [
                self.hmm_model.hmm_model.decode([[x] for x in trace])[1].tolist()
                for trace in self.hmm_model.train_traces
            ]
        else:
            raise NotImplementedError("Unknown model type!")

    def get_eval_result(self):
        val_traces = self.val_abstract_traces
        test_traces = self.test_abstract_traces

        ###################### Get the abnormal threshold ##############################
        if self.dataset == "truthful_qa":
            abnormal_threshold = 0.5
        else:
            # Get indices for random sampling
            num_samples = 100  # The number of random samples you want to choose
            if len(test_traces) < num_samples or len(val_traces) < num_samples:
                print("Not enough samples to choose from!")
                num_samples = min(len(test_traces), len(val_traces))

            # Choose random indices
            random_test_indices = random.sample(range(len(test_traces)), num_samples)
            random_val_indices = random.sample(range(len(val_traces)), num_samples)

            # Extract the random samples using the random indices
            selected_test_traces = [test_traces[i] for i in random_test_indices]
            selected_val_traces = [val_traces[i] for i in random_val_indices]

            selected_test_groundtruths = [1 for _ in random_test_indices]
            selected_val_groundtruths = [0 for _ in random_val_indices]
            selected_threshold_traces = selected_val_traces + selected_test_traces
            selected_threshold_groundtruths = (
                selected_val_groundtruths + selected_test_groundtruths
            )

            selected_abnormal_transition_positive_score_map = (
                self.prob_model.get_sentence_scores_by_transition_binding(
                    selected_threshold_traces, selected_threshold_groundtruths
                )
            )

            abnormal_y_pred, _ = self.prob_model.compose_scores_with_groundtruths_pair(
                selected_abnormal_transition_positive_score_map
            )

            abnormal_threshold = statistics.median(abnormal_y_pred)
        self.abnormal_threshold = abnormal_threshold
        print(
            "------------------ Abnormal Threshold: {} ------------------".format(
                abnormal_threshold
            )
        )
        ####### Analyze the test sentence_test_scores ##############
        val_test_traces = self.val_abstract_traces + self.test_abstract_traces
        val_test_groundtruths = (
            self.prob_model.val_groundtruths + self.prob_model.test_groundtruths
        )
        self.val_test_traces = val_test_traces
        self.val_test_groundtruths = val_test_groundtruths

        state_binding_dataset = [
            "truthful_qa",
            "mbpp",
            "humaneval",
            "code_search_net_java",
            "tl_code_sum",
        ]

        if self.dataset in state_binding_dataset:
            sentence_positive_score_map = (
                self.prob_model.get_sentence_scores_by_state_binding(
                    self.test_abstract_traces,
                    self.state_positive_prob_map,
                    self.prob_model.test_groundtruths,
                )
            )
        else:
            sentence_positive_score_map = (
                self.prob_model.get_sentence_scores_by_transition_binding(
                    val_test_traces, val_test_groundtruths
                )
            )

        ###################### prediction ##############################
        y_pred, y_groundtruth = self.prob_model.compose_scores_with_groundtruths_pair(
            sentence_positive_score_map
        )

        self.y_pred = y_pred
        self.y_groundtruth = y_groundtruth

        if self.dataset in state_binding_dataset:
            aucroc, tpr, fpr = self.prob_model.get_aucroc_by_state_binding()
        else:
            aucroc, tpr, fpr = self.prob_model.get_aucroc_by_transition_binding()

        self.aucroc = aucroc

        print(
            "------------------ AUCROC: {} ------------------".format(
                aucroc
            )
        )
        return aucroc, tpr, fpr

    # ===================== Semantic-aware Level =====================

    def preciseness(self):
        """
        Calculate the preciseness of the model's predictions.
        
        This method computes the absolute difference between the predicted values (`self.y_pred`)
        and the ground truth values (`self.y_groundtruth`). It then returns the area under the ROC curve 
        (assuming it's stored in `self.aucroc`) and the maximum absolute difference observed.
        
        Returns:
            tuple: A tuple containing the area under the ROC curve and the maximum absolute difference.
        """
        differences = np.abs(np.array(self.y_pred) - np.array(self.y_groundtruth))
        # Find the maximum difference
        max_difference = np.max(differences)
        return self.aucroc if self.aucroc > 0.5 else 1 - self.aucroc, max_difference

    def entropy(self):
        """
        Calculate the average entropy of the model's predictions for validation and test data.
        
        The method computes the entropy based on transition probabilities in the traces.
        The entropy is calculated for each trace and then averaged for validation and test datasets.
        
        Note: 
        - The abstract traces for testing are in `self.test_abstract_traces`.
        - The abstract traces for validation are in `self.val_abstract_traces`.
        
        Returns:
            tuple: A tuple containing the average entropy for validation and test data respectively.
        """
        def get_entropy(traces):
            entropy_list = []
            for i, trace in enumerate(traces):
                prob_list = []
                for j, state in enumerate(trace):
                    if j == len(trace) - 1:
                        break
                    next = trace[j + 1]
                    if (
                        state not in train_transition_probs
                        or next not in train_transition_probs[state]
                    ):
                        continue
                    prob_list.append(train_transition_probs[state][next])

                non_zero_v = [i for i in prob_list if i > 0]
                entropy = -np.sum(non_zero_v * np.log(non_zero_v))
                entropy_list.append(entropy)
            return entropy_list

        train_transition_probs = self.prob_model.train_transition_probs
        test_entropy_list = get_entropy(self.test_abstract_traces)
        val_entropy_list = get_entropy(self.val_abstract_traces)
        val_entropy = statistics.mean(val_entropy_list)
        test_entropy = statistics.mean(test_entropy_list)
        return val_entropy, test_entropy

    def _kl_divergence(self, P, Q):
        """
        Compute the Kullback-Leibler divergence between two matrices P and Q.
        Both matrices must have the same shape.
        """
        # Flatten the matrices
        P = P.flatten()
        Q = Q.flatten()

        # Ensure that the distributions are normalized (sum to 1)
        P = P / P.sum()
        Q = Q / Q.sum()

        # Compute KL divergence
        kl = np.sum(P * (np.log(P + 1e-10) - np.log(Q + 1e-10)))

        return kl

    def probabilistic_reasoning(self):
        """
        Compute the divergence between probabilistic reasoning and the training transition probabilities.
        
        The method calculates conditional probabilities for states in the abstract traces based on training transition probabilities. 
        A divergence measure is then calculated between the matrices of probabilistic reasoning and training transition probabilities.
        
        Note: 
        - The transition probabilities for training are assumed to be stored in `self.prob_model.train_transition_probs`.
        - The abstract traces for training are in `self.train_abstract_traces`.
        - The threshold for abnormality is in `self.abnormal_threshold`.
        
        Returns:
            float: The divergence measure between the probabilistic reasoning and training transition probabilities.
        """
        prob_reasoning_dict = {}
        TM = self.prob_model.train_transition_probs

        for trace in self.train_abstract_traces:
            for i, state in enumerate(trace):
                if i == len(trace) - 1:
                    break
                next = trace[i + 1]
                if state not in TM or next not in TM[state]:
                    conditional_prob = 0
                else:
                    # Probability that tau_i is "good"
                    p_state = sum(
                        prob
                        for _, prob in TM[state].items()
                        if prob > self.abnormal_threshold
                    )
                    # Probability that tau_{i+1} is "good"
                    p_next = sum(
                        prob
                        for end_state, prob in TM[next].items()
                        if prob > self.abnormal_threshold
                    )
                    # Conditional probability using the formula
                    conditional_prob = (
                        (TM[state][next] * p_state) / p_next if p_next > 0 else 0
                    )

                if state not in prob_reasoning_dict:
                    prob_reasoning_dict[state] = {}
                prob_reasoning_dict[state][next] = conditional_prob

        row_keys = set(prob_reasoning_dict.keys()) | set(TM.keys())
        col_keys = set(
            k for d in (prob_reasoning_dict, TM) for v in d.values() for k in v.keys()
        )

        n = max(len(row_keys), len(col_keys))
        row_key_to_idx = {key: idx for idx, key in enumerate(sorted(row_keys))}
        col_key_to_idx = {key: idx for idx, key in enumerate(sorted(col_keys))}

        prob_reasoning_matrix = np.zeros((n, n))
        TM_matrix = np.zeros((n, n))

        for outer_key, inner_dict in prob_reasoning_dict.items():
            for inner_key, value in inner_dict.items():
                prob_reasoning_matrix[
                    row_key_to_idx[outer_key], col_key_to_idx[inner_key]
                ] = value

        for outer_key, inner_dict in TM.items():
            for inner_key, value in inner_dict.items():
                TM_matrix[row_key_to_idx[outer_key], col_key_to_idx[inner_key]] = value

        prob_reasoning_divergence = self._kl_divergence(
            prob_reasoning_matrix, TM_matrix
        )
        return prob_reasoning_divergence

    # ===================== Semantics Space Diversity =====================
    def value_diversity_instant_level(self):
        """
        Compute the value diversity at an instant level for validation and test data.
        
        The method calculates the diversity based on transition probabilities in the traces.
        Diversity is computed differently depending on the ground truth values. The results are averaged for 
        validation and test datasets.
        
        Note: 
        - The transition probabilities are assumed to be stored in `self.prob_model.train_transition_probs`.
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        - Ground truths for validation and testing are stored in `self.prob_model.val_groundtruths` and `self.prob_model.test_groundtruths` respectively.
        
        Returns:
            tuple: A tuple containing the average value diversity for validation and test data respectively.
        """
        def get_result(traces, groundtruths):
            train_transition_probs = self.prob_model.train_transition_probs
            result = []
            for i, trace in enumerate(traces):
                prob_list = []
                for j, state in enumerate(trace):
                    if j == len(trace) - 1:
                        break
                    next = trace[j + 1]
                    if (
                        state not in train_transition_probs
                        or next not in train_transition_probs[state]
                    ):
                        continue
                    prob_list.append(train_transition_probs[state][next])
                if prob_list == []:
                    continue
                if groundtruths[i] == 0:
                    result.append(min(prob_list))
                else:
                    result.append(1 - max(prob_list))
            return statistics.mean(result) if len(result) > 0 else 0

        return get_result(
            self.val_abstract_traces, self.prob_model.val_groundtruths
        ), get_result(self.test_abstract_traces, self.prob_model.test_groundtruths)

    def value_diversity_n_gram_level(self):
        """
        Compute the value diversity at an n-gram level for validation and test data.
        
        The method calculates the diversity based on n-gram transition probabilities in the traces.
        Diversity is computed differently depending on the ground truth values. The results are 
        averaged for 2, 3, and 4-grams for both validation and test datasets.
        
        Note: 
        - The transition probabilities are assumed to be stored in `self.prob_model.train_transition_probs`.
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        - Ground truths for validation and testing are stored in `self.prob_model.val_groundtruths` and `self.prob_model.test_groundtruths` respectively.
        
        Returns:
            tuple: Two dictionaries containing the average value diversity for validation and test data respectively.
                Each dictionary has keys 2, 3, and 4 representing the n-gram level.
        """
        def get_result(traces, groundtruths):
            result = {2: [], 3: [], 4: []}
            n_list = result.keys()
            train_transition_probs = self.prob_model.train_transition_probs
            for n in n_list:
                for i, trace in enumerate(traces):
                    prob_list = []
                    for j, state in enumerate(trace):
                        if j == len(trace) - 1:
                            break
                        next = trace[j + 1]
                        if (
                            state not in train_transition_probs
                            or next not in train_transition_probs[state]
                        ):
                            continue
                        prob_list.append(train_transition_probs[state][next])
                    temp_n_gram_prob_list = []
                    for k in range(len(prob_list) - n + 1):
                        if groundtruths[i] == 0:
                            temp_n_gram_prob_list.append(sum(prob_list[k : k + n]))
                        else:
                            temp_n_gram_prob_list.append(n - sum(prob_list[k : k + n]))

                    result[n].append(statistics.mean(temp_n_gram_prob_list)) if len(
                        temp_n_gram_prob_list
                    ) > 0 else 0
                result[n] = statistics.mean(result[n]) if len(result[n]) > 0 else 0
            return result

        test_result = get_result(
            self.test_abstract_traces, self.prob_model.test_groundtruths
        )
        val_result = get_result(
            self.val_abstract_traces, self.prob_model.val_groundtruths
        )
        return val_result, test_result

    def _get_derivative_sign_n_gram(self, prob_list, n):
        # get left derivative signs
        temp_n_gram_prob_list = []
        for i in range(len(prob_list) - n + 1):
            temp_n_gram_prob_list.append(sum(prob_list[i : i + n]))
        diff = 0
        for i in range(1, len(temp_n_gram_prob_list)):
            diff += temp_n_gram_prob_list[i] - temp_n_gram_prob_list[i - 1]
        return diff

    def derivative_diversity_n_gram_level(self):
        """
        Compute the derivative diversity at an n-gram level for validation and test data.
        
        The method calculates the diversity based on the derivatives of n-gram transition probabilities in the traces.
        Results are computed for increasing and decreasing trends. The results are averaged for 2, 3, and 4-grams 
        for both validation and test datasets.
        
        Note: 
        - The transition probabilities are assumed to be stored in `self.prob_model.train_transition_probs`.
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        
        Returns:
            tuple: Four dictionaries containing the average derivative diversity for validation (increasing and decreasing)
                and test data (increasing and decreasing) respectively. Each dictionary has keys 2, 3, and 4 representing 
                the n-gram level.
        """
        def get_result(traces):
            increasing_result = {2: 0, 3: 0, 4: 0}
            decreasing_result = {2: 0, 3: 0, 4: 0}
            n_list = decreasing_result.keys()

            train_transition_probs = self.prob_model.train_transition_probs
            for n in n_list:
                left_derivative_signs = []
                for i, trace in enumerate(traces):
                    prob_list = []
                    for j, state in enumerate(trace):
                        if j == len(trace) - 1:
                            break
                        next = trace[j + 1]
                        if (
                            state not in train_transition_probs
                            or next not in train_transition_probs[state]
                        ):
                            continue
                        prob_list.append(train_transition_probs[state][next])

                    diff = self._get_derivative_sign_n_gram(prob_list, n)
                    left_derivative_signs.append(diff)

                increasing_result[n] = max(left_derivative_signs)
                decreasing_result[n] = min(left_derivative_signs)
            return increasing_result, decreasing_result

        val_result_increasing, val_result_decreasing = get_result(
            self.val_abstract_traces
        )
        test_result_increasing, test_result_decreasing = get_result(
            self.test_abstract_traces
        )
        return (
            val_result_increasing,
            val_result_decreasing,
            test_result_increasing,
            test_result_decreasing,
        )

    def second_derivative_diversity_n_gram_level(self):
        def get_result(traces):
            train_transition_probs = self.prob_model.train_transition_probs
            increasing_result = {2: 0, 3: 0, 4: 0}
            decreasing_result = {2: 0, 3: 0, 4: 0}
            n_list = decreasing_result.keys()
            for n in n_list:
                left_derivative_signs = []
                for i, trace in enumerate(traces):
                    prob_list = []
                    for j, state in enumerate(trace):
                        if j == len(trace) - 1:
                            break
                        next = trace[j + 1]
                        if (
                            state not in train_transition_probs
                            or next not in train_transition_probs[state]
                        ):
                            continue
                        prob_list.append(train_transition_probs[state][next])

                    diff = self._get_derivative_sign_n_gram(prob_list, n)
                    left_derivative_signs.append(diff)
                sec_derivative_signs = []
                for i in range(1, len(left_derivative_signs)):
                    sec_derivative_signs.append(
                        left_derivative_signs[i] - left_derivative_signs[i - 1]
                    )

                increasing_result[n] = max(sec_derivative_signs)
                decreasing_result[n] = min(sec_derivative_signs)
            return increasing_result, decreasing_result

        val_result_increasing, val_result_decreasing = get_result(
            self.val_abstract_traces
        )
        test_result_increasing, test_result_decreasing = get_result(
            self.test_abstract_traces
        )
        return (
            val_result_increasing,
            val_result_decreasing,
            test_result_increasing,
            test_result_decreasing,
        )

    def sliding_window(self, sequence, window_size):
        """Generate sub-sequences of window_size from sequence."""

    def count_subsequences(self, traces, window_size):
        """Count the occurrence of each sub-sequence of window_size in traces."""
        counter = Counter()
        for trace in traces:
            for subsequence in self.sliding_window(trace, window_size):
                # Convert list of integers to a hashable type to count them
                subsequence_tuple = tuple(subsequence)
                counter[subsequence_tuple] += 1
        return counter

    def _calculate_radius(self, cluster_method, data, reference_radius=None):
        if cluster_method == "KMeans":
            cluster_centers = (
                self.abstractStateExtraction.cluster_model.cluster_centers_
            )
        elif cluster_method == "GMM":
            cluster_centers = self.abstractStateExtraction.cluster_model.means_
        else:
            raise ValueError("Unknown cluster method: %s" % cluster_method)
        max_radius = 0
        exceeding_count = 0
        for i, center in enumerate(cluster_centers):
            cur_cluster = i + 1
            if cur_cluster not in data:
                continue
            distances = pairwise_distances(data[cur_cluster], [center])
            max_radius_cluster = distances.max()
            max_radius = max(max_radius, max_radius_cluster)

            if reference_radius is not None:
                exceeding_count += (distances > reference_radius).sum()
        return max_radius, exceeding_count

    # ===================== Model-aware =====================

    def succinctness(self):
        """
        Compute the succinctness measure based on the ratio of abstract states to concrete states.
        
        The method calculates the number of abstract states and the total number of concrete states
        in the training instances. The succinctness is then defined as the ratio of these two numbers.
        
        Note: 
        - The number of abstract states is assumed to be stored in `self.abstractStateExtraction.args.abstract_state`.
        - The training instances are in `self.abstractStateExtraction.train_instances`.
        
        Returns:
            float: The succinctness measure.
        """
        num_abs_states = self.abstractStateExtraction.args.abstract_state
        num_concrete_states = sum(
            [
                len(i["state_trace"])
                for i in self.abstractStateExtraction.train_instances
            ]
        )

        result = num_abs_states / num_concrete_states

        return result

    def transition_MMD_instance_level(self):
        """
        Compute the Maximum Mean Discrepancy (MMD) at instance level between validation and test data transitions.
        
        The method calculates the MMD based on transition distributions derived from the abstract traces.
        MMD provides a measure of the difference between two distributions. Here, it is used to compare the 
        transition distributions between validation and test data.
        
        Note: 
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        - The transition probabilities are assumed to be stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            float: The computed Maximum Mean Discrepancy between validation and test transition distributions.
        """
        def get_transition_distribution(traces):
            transition_matrix = {}
            for trace in traces:
                for i in range(len(trace) - 1):
                    state = trace[i]
                    next = trace[i + 1]
                    if state not in transition_matrix:
                        transition_matrix[state] = {}
                    else:
                        if next not in transition_matrix[state]:
                            transition_matrix[state][next] = 1
                        else:
                            transition_matrix[state][next] += 1
                for state in transition_matrix:
                    total = sum(transition_matrix[state].values())
                    for next in transition_matrix[state]:
                        transition_matrix[state][next] /= total
            return transition_matrix

        def MMD(x, y, kernel):
            """Emprical maximum mean discrepancy. The lower the result
            the more evidence that distributions are the same.

            Args:
                x: first sample, distribution P
                y: second sample, distribution Q
                kernel: kernel type such as "multiscale" or "rbf"
            """
            xx, yy, zz = torch.mm(x, x.t()), torch.mm(y, y.t()), torch.mm(x, y.t())
            rx = xx.diag().unsqueeze(0).expand_as(xx)
            ry = yy.diag().unsqueeze(0).expand_as(yy)

            dxx = rx.t() + rx - 2.0 * xx  # Used for A in (1)
            dyy = ry.t() + ry - 2.0 * yy  # Used for B in (1)
            dxy = rx.t() + ry - 2.0 * zz  # Used for C in (1)

            XX, YY, XY = (
                torch.zeros(xx.shape).to(device),
                torch.zeros(xx.shape).to(device),
                torch.zeros(xx.shape).to(device),
            )

            if kernel == "multiscale":
                bandwidth_range = [0.2, 0.5, 0.9, 1.3]
                for a in bandwidth_range:
                    XX += a**2 * (a**2 + dxx) ** -1
                    YY += a**2 * (a**2 + dyy) ** -1
                    XY += a**2 * (a**2 + dxy) ** -1

            if kernel == "rbf":
                bandwidth_range = [10, 15, 20, 50]
                for a in bandwidth_range:
                    XX += torch.exp(-0.5 * dxx / a)
                    YY += torch.exp(-0.5 * dyy / a)
                    XY += torch.exp(-0.5 * dxy / a)
            return torch.mean(XX + YY - 2.0 * XY)

        min_length = min(len(self.val_abstract_traces), len(self.test_abstract_traces))

        test_traces = self.test_abstract_traces[:min_length]
        val_traces = self.val_abstract_traces[:min_length]

        test_matrix = get_transition_distribution(test_traces)
        val_matrix = get_transition_distribution(val_traces)
        for state in test_matrix:
            if state not in val_matrix:
                val_matrix[state] = {}
            for next in test_matrix[state]:
                if next not in val_matrix[state]:
                    val_matrix[state][next] = 1e-7
        for state in val_matrix:
            if state not in test_matrix:
                test_matrix[state] = {}
            for next in val_matrix[state]:
                if next not in test_matrix[state]:
                    test_matrix[state][next] = 1e-7
        test_distribution = []
        val_distribution = []
        for state in test_matrix:
            for next in test_matrix[state]:
                if test_matrix[state][next] == 1e-7 and val_matrix[state][next] == 1e-7:
                    continue
                test_distribution.append(test_matrix[state][next])
                val_distribution.append(val_matrix[state][next])

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        tensor_test = torch.tensor(test_distribution, dtype=torch.float32).to(device)
        tensor_val = torch.tensor(val_distribution, dtype=torch.float32).to(device)

        tensor_val = tensor_val.view(-1, 1)
        tensor_test = tensor_test.view(-1, 1)
        # Calculate the three terms in the MMD formula
        mmd = MMD(tensor_val, tensor_test, kernel="multiscale")
        mmd = mmd.cpu().numpy()
        return mmd

    def transition_KL_divergence_instance_level(self):
        """
        Compute the Kullback-Leibler (KL) divergence at instance level between validation and test data transitions.
        
        The method calculates the KL divergence based on transition distributions derived from the abstract traces.
        KL divergence provides a measure of the difference between two probability distributions. Here, it is 
        used to compare the transition distributions between validation and test data at an instance level.
        
        Note: 
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        - The training transition probabilities are stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            list: A list of KL divergence values for each instance in the validation and test data.
        """
        def get_transition_distribution_from_traces(traces):
            result = []
            for trace in traces:
                TM = self.prob_model.train_transition_probs
                transition_matrix = {}
                for i in range(len(trace) - 1):
                    state = trace[i]
                    next = trace[i + 1]
                    if state not in transition_matrix:
                        transition_matrix[state] = {}
                    else:
                        if next not in transition_matrix[state]:
                            transition_matrix[state][next] = 1
                        else:
                            transition_matrix[state][next] += 1
                flat_transition = []
                for tm_state in TM.keys():
                    if tm_state not in transition_matrix:
                        transition_matrix[tm_state] = {}
                    for tm_next in TM[tm_state].keys():
                        if tm_next not in transition_matrix[tm_state]:
                            transition_matrix[tm_state][tm_next] = 1e-7
                        else:
                            transition_matrix[tm_state][tm_next] = transition_matrix[
                                tm_state
                            ][tm_next] / len(trace)
                        flat_transition.append(transition_matrix[tm_state][tm_next])

                result.append(flat_transition)
            return result

        min_length = min(len(self.val_abstract_traces), len(self.test_abstract_traces))

        test_traces = self.test_abstract_traces[:min_length]
        val_traces = self.val_abstract_traces[:min_length]

        test_ditribution = get_transition_distribution_from_traces(test_traces)
        val_distribution = get_transition_distribution_from_traces(val_traces)
        result = []
        for i in range(min_length):
            instance_min_length = min(
                len(test_ditribution[i]), len(val_distribution[i])
            )
            test_distribution_instance = test_ditribution[i][:instance_min_length]
            val_distribution_instance = val_distribution[i][:instance_min_length]

            test_instance = np.array(test_distribution_instance)
            val_instance = np.array(val_distribution_instance)
            normal = np.sum(kl_div(test_instance, val_instance))
            abnormal = np.sum(kl_div(val_instance, test_instance))
            avg_div = (normal + abnormal) / 2
            result.append(avg_div)
        return result

    def transition_matrix_list(self):
        state_binding_datasets = [
            "truthful_qa",
            "humaneval",
            "mbpp",
            "tl_code_sum",
            "code_search_net_java"
        ]
        
        def get_transition_distribution_by_traces(traces):
            transition_matrix = {}
            for trace in traces:
                for i in range(len(trace) - 1):
                    state = trace[i]
                    next = trace[i + 1]
                    if state not in transition_matrix:
                        transition_matrix[state] = {}
                    else:
                        if next not in transition_matrix[state]:
                            transition_matrix[state][next] = 1
                        else:
                            transition_matrix[state][next] += 1
            for state in transition_matrix:
                total = sum(transition_matrix[state].values())
                for next in transition_matrix[state]:
                    transition_matrix[state][next] /= total
            return transition_matrix

        if self.dataset in state_binding_datasets:
            test_abnormal_abstract_traces = []
            test_normal_abstract_traces = []
            train_abstract_traces = []
            for i in range(len(self.abstractStateExtraction.train_instances)):
                if self.abstractStateExtraction.train_instances[i]["binary_label"] == 1:
                    train_abstract_traces.append(self.train_abstract_traces[i])
                else:
                    test_abnormal_abstract_traces.append(self.train_abstract_traces[i])
            for i in range(len(self.abstractStateExtraction.test_instances)):
                if self.abstractStateExtraction.test_instances[i]["binary_label"] == 1:
                    test_normal_abstract_traces.append(self.test_abstract_traces[i])
                else:
                    test_abnormal_abstract_traces.append(self.test_abstract_traces[i])
            for i in range(len(self.abstractStateExtraction.val_instances)):
                if self.abstractStateExtraction.val_instances[i]["binary_label"] == 1:
                    test_normal_abstract_traces.append(self.val_abstract_traces[i])
                else:
                    test_abnormal_abstract_traces.append(self.val_abstract_traces[i])

        else:
            test_abnormal_abstract_traces = self.test_abstract_traces
            test_normal_abstract_traces = self.val_abstract_traces
            train_abstract_traces = self.train_abstract_traces
        test_distribution = get_transition_distribution_by_traces(
            test_abnormal_abstract_traces
        )
        val_distribution = get_transition_distribution_by_traces(
            test_normal_abstract_traces
        )
        train_distribution = get_transition_distribution_by_traces(
            train_abstract_traces
        )

        # for state in test_distribution:
        #     if state not in val_distribution:
        #         val_distribution[state] = {}
        #     for next in test_distribution[state]:
        #         if next not in val_distribution[state]:
        #             val_distribution[state][next] = 1e-7
        # for state in val_distribution:
        #     if state not in test_distribution:
        #         test_distribution[state] = {}
        #     for next in val_distribution[state]:
        #         if next not in test_distribution[state]:
        #             test_distribution[state][next] = 1e-7

        for state in val_distribution:
            if state not in train_distribution:
                train_distribution[state] = {}
            for next in val_distribution[state]:
                if next not in train_distribution[state]:
                    train_distribution[state][next] = 1e-7

        for state in train_distribution:
            if state not in val_distribution:
                val_distribution[state] = {}
            for next in train_distribution[state]:
                if next not in val_distribution[state]:
                    val_distribution[state][next] = 1e-7

        test_distribution_list = []
        val_distribution_list = []
        for state in test_distribution:
            for next in test_distribution[state]:
                if (
                    test_distribution[state][next] == 1e-7
                    and val_distribution[state][next] == 1e-7
                ):
                    continue
                test_distribution_list.append(test_distribution[state][next])
                
        train_distribution_list = []
        for state in train_distribution:
            for next in train_distribution[state]:
                train_distribution_list.append(train_distribution[state][next])
        
        for state in val_distribution:
            for next in val_distribution[state]:
                val_distribution_list.append(val_distribution[state][next])

        return train_distribution_list, val_distribution_list, test_distribution_list

    def transition_gain(self):
        """
        Compute the transition gain between validation and test data transitions.
        
        The method calculates the transition gain based on coverage differences in the abstract traces. 
        Transition gain is computed as the difference in coverage between validation and test data for each state transition.
        
        Note: 
        - The abstract traces for testing are in `self.test_abstract_traces`, and for validation are in `self.val_abstract_traces`.
        - The training transition probabilities are stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            tuple: 
                - A dictionary representing the transition gain for each state transition.
                - A dictionary representing the coverage of each state transition in the validation data.
                - A dictionary representing the coverage of each state transition in the test data.
        """
        def get_transition_coverage_from_traces(traces, state, next, delta):
            num_traces = 0
            for trace in traces:
                cur_transition_count = 0
                for i in range(len(trace) - 1):
                    if state == trace[i] and next == trace[i + 1]:
                        cur_transition_count += 1
                if cur_transition_count / len(trace) >= delta:
                    num_traces += 1
            return num_traces / len(traces)

        transition_gain_dict = {}
        normal_coverage_dict = {}
        abnormal_coverage_dict = {}

        delta = 0.5
        TM = self.prob_model.train_transition_probs
        test_traces = self.test_abstract_traces
        val_traces = self.val_abstract_traces
        for state in TM.keys():
            if state not in transition_gain_dict:
                transition_gain_dict[state] = {}
                normal_coverage_dict[state] = {}
                abnormal_coverage_dict[state] = {}
            for next in TM[state].keys():
                if next not in transition_gain_dict[state]:
                    current_test_transition_coverage = (
                        get_transition_coverage_from_traces(
                            test_traces, state, next, delta
                        )
                    )
                    current_val_transition_coverage = (
                        get_transition_coverage_from_traces(
                            val_traces, state, next, delta
                        )
                    )

                    normal_coverage_dict[state][next] = current_val_transition_coverage
                    abnormal_coverage_dict[state][
                        next
                    ] = current_test_transition_coverage

                    transition_gain_dict[state][next] = (
                        current_val_transition_coverage
                        - current_test_transition_coverage
                    )
        return transition_gain_dict, normal_coverage_dict, abnormal_coverage_dict

    def state_coverage(self):
        train_pca = self.abstractStateExtraction.pca_train
        test_pca = self.abstractStateExtraction.pca_test
        cluster_labels_train = self.abstractStateExtraction.cluster_train
        cluster_labels_test = self.abstractStateExtraction.cluster_test
        cluster_method = self.abstractStateExtraction.args.cluster_method
        train_set = {}
        test_set = {}

        # Get State Coverage
        if cluster_method == "Grid":
            stacked_pca_traces = np.vstack(train_pca)
            lbd = np.min(stacked_pca_traces, axis=0)
            ubd = np.max(stacked_pca_traces, axis=0)

            # Count how many times pca_test is outside the bounds
            out_of_bounds_count = 0
            total_count = 0
            for test_point in test_pca:
                for p in test_point:
                    if (p < lbd).any() or (p > ubd).any():
                        out_of_bounds_count += 1
                    total_count += 1

            state_coverage = 1 - (out_of_bounds_count / total_count)

        else:
            for i, label in enumerate(cluster_labels_train):
                if label not in train_set:
                    train_set[label] = [train_pca[i]]
                else:
                    train_set[label].append(train_pca[i])
            for i, label in enumerate(cluster_labels_test):
                if label not in test_set:
                    test_set[label] = [test_pca[i]]
                else:
                    test_set[label].append(test_pca[i])
            # Get test count from test_pca np matrix
            test_count = test_pca.shape[0] * test_pca.shape[1]
            train_radius, _ = self._calculate_radius(cluster_method, train_set)
            test_radius, exceeding_count = self._calculate_radius(
                cluster_method, test_set, train_radius
            )
            state_coverage = (test_count - exceeding_count) / test_count

        return state_coverage

    def sensitivity(self):
        """
        Compute the sensitivity of the model by perturbing the test data and measuring the effect.
        
        The method perturbs the hidden information from the test data and checks the difference 
        in the abstract state representations between the original and perturbed data. The 
        sensitivity is represented as the percentage of difference in the state representations.
        
        Note: 
        - The hidden information for testing is in `self.abstractStateExtraction.test_hidden_info`.
        - The PCA transformation model is stored in `self.abstractStateExtraction.pca_model`.
        - The clustering method used can be accessed via `self.abstractStateExtraction.args.cluster_method`.
        
        Returns:
            float: The sensitivity measure represented as the percentage difference in state representations.
        """
        epsilon = 0.1
        test_hidden_info = self.abstractStateExtraction.test_hidden_info

        np_test_hidden_info = np.concatenate(test_hidden_info, axis=0)
        np_test_hidden_info_copy = np_test_hidden_info.copy()
        np_test_hidden_info_perturb = np_test_hidden_info_copy + epsilon
        if self.abstractStateExtraction.args.cluster_method == "Grid":
            train_pca = self.abstractStateExtraction.pca_train
            test_hidden_info_perturb = [x + epsilon for x in test_hidden_info]
            pca_test_data_perturb = []
            for i in range(len(test_hidden_info_perturb)):
                pca_test_data_perturb.append(
                    self.abstractStateExtraction.pca_model.transform(
                        test_hidden_info_perturb[i]
                    )
                )
            pca_test_data_original = []
            for i in range(len(test_hidden_info)):
                pca_test_data_original.append(
                    self.abstractStateExtraction.pca_model.transform(
                        test_hidden_info[i]
                    )
                )
            regular_grid = RegularGrid(
                self.abstractStateExtraction.args.abstract_state,
                self.abstractStateExtraction.args.grid_history_dependency_num,
            )

            stacked_pca_traces = np.vstack(train_pca)
            lbd = np.min(stacked_pca_traces, axis=0)
            ubd = np.max(stacked_pca_traces, axis=0)
            grid = Grid(
                lbd, ubd, self.abstractStateExtraction.args.grid_history_dependency_num
            )

            test_perturb_abst_traces = regular_grid.pca_to_abstract_traces(
                grid, pca_test_data_perturb
            )
            test_original_abst_traces = regular_grid.pca_to_abstract_traces(
                grid, pca_test_data_original
            )

            cluster_labels_test_perturb = [
                item for sublist in test_perturb_abst_traces for item in sublist
            ]
            cluster_labels_test_original = [
                item for sublist in test_original_abst_traces for item in sublist
            ]
            different_count = sum(
                a != b
                for a, b in zip(
                    cluster_labels_test_original, cluster_labels_test_perturb
                )
            )
            percentage_difference = different_count / len(cluster_labels_test_perturb)

        else:
            pca_test_data_perturb = self.abstractStateExtraction.pca_model.transform(
                np_test_hidden_info_perturb
            )

            cluster_labels_test_perturb = (
                self.abstractStateExtraction.cluster_model.predict(
                    pca_test_data_perturb
                )
            )
            different_count = sum(
                a != b
                for a, b in zip(
                    self.abstractStateExtraction.cluster_test,
                    cluster_labels_test_perturb,
                )
            )
            percentage_difference = different_count / len(cluster_labels_test_perturb)
        return percentage_difference

    # ===================== State Level =====================
    def sink_state(self):
        """
        Compute the ratio of sink states in the transition probability matrix.
        
        A sink state is defined as a state transition where the probability of transitioning 
        from one state to another is 1. This method identifies such transitions and computes 
        the ratio of sink states relative to the total number of states.
        
        Note: 
        - The training transition probabilities are stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            float: The ratio of sink states to the total number of states.
        """
        train_transition_probs = self.prob_model.train_transition_probs
        sink_state = []
        total_state_num = 0
        for i, row in train_transition_probs.items():
            for j, value in row.items():
                if value == 1:
                    sink_state.append((i, j))
                total_state_num += 1
        return len(sink_state) / total_state_num

    def source_state(self):
        """
        Compute the ratio of source states in the transition probability matrix.
        
        A source state is defined as a state transition where the probability of transitioning 
        from one state to another is 0, but the reverse transition has a non-zero probability. 
        This method identifies such transitions and computes the ratio of source states relative 
        to the total number of states.
        
        Note: 
        - The training transition probabilities are stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            float: The ratio of source states to the total number of states.
        """
        train_transition_probs = self.prob_model.train_transition_probs
        source_state = []
        total_state_num = 0
        for i, row in train_transition_probs.items():
            for j, value in row.items():
                if (
                    value == 0
                    and j in train_transition_probs
                    and i in train_transition_probs[j]
                    and train_transition_probs[j][i] != 0
                ):
                    source_state.append((i, j))
                total_state_num += 1
        return len(source_state) / total_state_num

    def recurrent_state(self):
        """
        Compute the ratio of recurrent states in the transition probability matrix.
        
        A recurrent state is defined as a state transition where the probability of transitioning 
        from one state to another is non-zero and the reverse transition also has a non-zero probability. 
        This method identifies such transitions and computes the ratio of recurrent states relative 
        to the total number of states.
        
        Note: 
        - The training transition probabilities are stored in `self.prob_model.train_transition_probs`.
        
        Returns:
            float: The ratio of recurrent states to the total number of states.
        """
        train_transition_probs = self.prob_model.train_transition_probs
        recurrent_state = []
        total_state_num = 0
        for i, row in train_transition_probs.items():
            for j, value in row.items():
                if (
                    value != 0
                    and j in train_transition_probs
                    and i in train_transition_probs[j]
                    and train_transition_probs[j][i] != 0
                ):
                    recurrent_state.append((i, j))
                total_state_num += 1
        return len(recurrent_state) / total_state_num

    def _create_low_entropy_matrix(self, n):
        # Create a matrix where the diagonal (same state transition) is 0.95
        # and the remaining probability is spread among other states
        P_matrix = np.full((n, n), 0.05 / (n - 1))
        np.fill_diagonal(P_matrix, 0.95)
        return P_matrix

    def _create_high_entropy_matrix(self, n):
        # Create a matrix where each element is 1/n
        return np.full((n, n), 1 / n)

    def _calculate_entropy(self, P_matrix):
        # Ensure the matrix is square
        assert P_matrix.shape[0] == P_matrix.shape[1], "Matrix must be square"

        # Calculate stationary distribution
        P_matrix_mod = P_matrix.T - np.eye(P_matrix.shape[0])
        P_matrix_mod = np.vstack([P_matrix_mod, np.ones(P_matrix.shape[0])])
        b = np.zeros(P_matrix.shape[0])
        b = np.append(b, 1)
        stationary_vector = np.linalg.lstsq(P_matrix_mod, b, rcond=None)[0]

        # Compute transition entropy for each state and sum them
        total_entropy = 0
        for i in range(P_matrix.shape[0]):
            entropy_i = -np.sum(
                stationary_vector[i] * P_matrix[i, :] * np.log(P_matrix[i, :] + 1e-7)
            )
            total_entropy += entropy_i

        return total_entropy

    def stationary_distribution_entropy(self):
        TM = self.prob_model.train_transition_probs
        states = list(TM.keys())

        for start in states:
            # Check for a row with all zero values
            if not any(TM[start].values()):
                print(f"Row corresponding to key {start} has a sum of 0")

            # Fill missing end states with 0
            for end in states:
                TM[start].setdefault(end, 0)

        P_matrix = np.array([[TM[start][end] for end in states] for start in states])

        stationary_distribution_entropy = self._calculate_entropy(P_matrix)
        lower_bound_entropy = self._calculate_entropy(
            self._create_low_entropy_matrix(len(states))
        )
        upper_bound_entropy = self._calculate_entropy(
            self._create_high_entropy_matrix(len(states))
        )

        result = {
            "stationary_distribution_entropy": stationary_distribution_entropy,
            "lower_bound_entropy": lower_bound_entropy,
            "upper_bound_entropy": upper_bound_entropy,
        }

        return result

    def perplexity_llm(self):
        """
        Compute the perplexity for good (training) and bad (test) instances.
        
        The method calculates perplexity based on the probability distributions derived 
        from the training and test instances. Perplexity is a measure of how well a 
        probability distribution predicts a sample and is used often in the context 
        of natural language processing. Here, it's used to evaluate the model's predictions.
        
        Note: 
        - The training instances are stored in `self.abstractStateExtraction.train_instances`.
        - The test instances are stored in `self.abstractStateExtraction.test_instances`.
        
        Returns:
            tuple: A tuple containing the perplexity for good (training) and bad (test) instances respectively.
        """
        good_probs_list = [p for i in self.abstractStateExtraction.train_instances for p in i["probs"]]
        bad_probs_list = [p for i in self.abstractStateExtraction.test_instances for p in i["probs"]]
        good_probs = []
        bad_probs = []
        for l in good_probs_list:
            for p in l:
                if p == 0:
                    p = 1e-7
                good_probs.append(p)
        for l in bad_probs_list:
            for p in l:
                if p == 0:
                    p = 1e-7
                bad_probs.append(p)

        good_perplexity = np.exp(-np.sum(np.log(good_probs)) / len(good_probs))
        bad_perplexity = np.exp(-np.sum(np.log(bad_probs)) / len(bad_probs))
        return good_perplexity, bad_perplexity

    def smoothed_perplexity_llm(self):
        """
        Compute the smoothed perplexity for good (training) and bad (test) instances.
        
        The method calculates smoothed perplexity based on the probability distributions derived 
        from the training and test instances. The smoothing is applied using additive (Laplace) 
        smoothing. The perplexity is then computed for different vocabulary sizes (2, 3, and 4).
        
        Note: 
        - The training instances are stored in `self.abstractStateExtraction.train_instances`.
        - The test instances are stored in `self.abstractStateExtraction.test_instances`.
        
        Returns:
            dict: A dictionary where keys are vocabulary sizes (2, 3, 4) and values are tuples containing 
                the smoothed perplexity for good (training) and bad (test) instances respectively.
        """
        alpha = 0.5
        vocab_size = [2, 3, 4]
        result = {}
        for size in vocab_size:
            good_probs = []
            bad_probs = []
            for i in self.abstractStateExtraction.train_instances:
                for l in i["probs"]:
                    for p in l:
                        prob = (p + alpha) / (1 + alpha * size)
                        good_probs.append(prob)

            for i in self.abstractStateExtraction.test_instances:
                for l in i["probs"]:
                    for p in l:
                        prob = (p + alpha) / (1 + alpha * size)
                        bad_probs.append(prob)

            good_perplexity = np.exp(-np.sum(np.log(good_probs)) / len(good_probs))
            bad_perplexity = np.exp(-np.sum(np.log(bad_probs)) / len(bad_probs))

            result[size] = (good_perplexity, bad_perplexity)
        return result

    def perplexity_abstract_model(self):
        """
        Compute the perplexity for validation and test traces based on the abstract model's transition probabilities.
        
        The method calculates perplexity for the abstract traces using the transition probabilities of 
        the abstract model. Perplexity is a measure of how well a probability distribution predicts a sample.
        
        Note: 
        - The transition probabilities of the abstract model are stored in `self.prob_model.train_transition_probs`.
        - The validation traces are in `self.val_abstract_traces`.
        - The test traces are in `self.test_abstract_traces`.
        
        Returns:
            tuple: A tuple containing the perplexity for validation and test traces respectively.
        """
        def get_trace_transition_probs(traces):
            one_set_score_list = []
            for i, one_trace in enumerate(traces):
                if len(one_trace) < 2:
                    continue
                for j, start_state in enumerate(one_trace):
                    if j + 1 < len(one_trace):
                        end_state = one_trace[j + 1]
                    if (start_state in self.prob_model.train_transition_probs) and (
                        end_state in self.prob_model.train_transition_probs[start_state]
                    ):
                        score = self.prob_model.train_transition_probs[start_state][
                            end_state
                        ]
                        one_set_score_list.append(score)
                    else:
                        one_set_score_list.append(0.0)
            return one_set_score_list

        val_traces = self.val_abstract_traces
        test_traces = self.test_abstract_traces

        val_probs = get_trace_transition_probs(val_traces)
        test_probs = get_trace_transition_probs(test_traces)

        val_perplexity = np.exp(-np.sum(np.log(val_probs)) / len(val_probs))
        test_perplexity = np.exp(-np.sum(np.log(test_probs)) / len(test_probs))
        return val_perplexity, test_perplexity

    def smoothed_perplexity_abstract_model(self):
        """
        Compute the smoothed perplexity for validation and test traces based on the abstract model's transition probabilities.
        
        The method calculates smoothed perplexity for the abstract traces using the transition probabilities of 
        the abstract model. The smoothing is applied using additive (Laplace) smoothing. The perplexity is then 
        computed for different vocabulary sizes (2, 3, and 4).
        
        Note: 
        - The transition probabilities of the abstract model are stored in `self.prob_model.train_transition_probs`.
        - The validation traces are in `self.val_abstract_traces`.
        - The test traces are in `self.test_abstract_traces`.
        
        Returns:
            dict: A dictionary where keys are vocabulary sizes (2, 3, 4) and values are tuples containing 
                the smoothed perplexity for validation and test traces respectively.
        """
        def get_trace_transition_probs(traces):
            one_set_score_list = []
            for i, one_trace in enumerate(traces):
                if len(one_trace) < 2:
                    continue
                for j, start_state in enumerate(one_trace):
                    if j + 1 < len(one_trace):
                        end_state = one_trace[j + 1]
                    if (start_state in self.prob_model.train_transition_probs) and (
                        end_state in self.prob_model.train_transition_probs[start_state]
                    ):
                        score = self.prob_model.train_transition_probs[start_state][
                            end_state
                        ]
                        one_set_score_list.append(score)
                    else:
                        one_set_score_list.append(0.0)
            return one_set_score_list

        val_traces = self.val_abstract_traces
        test_traces = self.test_abstract_traces
        alpha = 0.5
        vocab_size = [2, 3, 4]
        result = {}
        val_probs = get_trace_transition_probs(val_traces)
        test_probs = get_trace_transition_probs(test_traces)
        for size in vocab_size:
            good_probs = []
            bad_probs = []
            for p in val_probs:
                prob = (p + alpha) / (1 + alpha * size)
                good_probs.append(prob)

            for p in test_probs:
                prob = (p + alpha) / (1 + alpha * size)
                bad_probs.append(prob)

            good_perplexity = np.exp(-np.sum(np.log(good_probs)) / len(good_probs))
            bad_perplexity = np.exp(-np.sum(np.log(bad_probs)) / len(bad_probs))

            result[size] = (good_perplexity, bad_perplexity)
        return result
