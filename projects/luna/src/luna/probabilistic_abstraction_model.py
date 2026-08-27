from luna.utils.interfaces import load_lists
from hmmlearn import hmm
import numpy as np
from sklearn import metrics
from scipy import interpolate
import os
import pickle

class ProbabilisticModel:
    def __init__(
        self,
        dataset,
        extract_block_idx,
        info_type,
        cluster_method,
        abstract_state,
        pca_dim,
        test_ratio,
        is_attack_success,
        grid_history_dependency_num,
        result_eval_path,
    ):
        """
        Initialize the ProbabilisticModel class.
        
        Parameters:
            dataset (str): The name of the dataset being used.
            extract_block_idx (int): Index to determine which block to extract information from.
            info_type (str): Type of information to be extracted (e.g., 'hidden_states', 'attention').
            cluster_method (str): The clustering method used for state abstraction (e.g., 'Grid', 'GMM', 'KMeans').
            abstract_state (int): The number of abstract states.
            pca_dim (int): The number of dimensions for PCA reduction.
            test_ratio (float): Ratio of the dataset to be used for testing.
            is_attack_success (bool): Flag to determine if the attack was successful.
            grid_history_dependency_num (int): The number of history dependencies for the grid clustering method.
            
        Attributes:
            train_groundtruths: Ground truth values for training instances.
            val_groundtruths: Ground truth values for validation instances.
            test_groundtruths: Ground truth values for test instances.
            train_traces: State traces for training instances.
            val_traces: State traces for validation instances.
            test_traces: State traces for test instances.
            
        Notes:
            - The method initializes various instance attributes based on the provided arguments.
            - It constructs the path to the evaluation folder based on the dataset and other parameters.
            - The method also analyzes the length distribution of state traces in the training, validation, and test sets.
        """

        groundtruths_key_dataset_map = {
            # "truthful_qa": "is_loop_generated",
            # "sst2": "is_loop_generated",
            # "advglue++": "is_loop_generated",
            "truthful_qa": "binary_label",
            "sst2": "is_id",
            "advglue++": "is_original",
            "humaneval": "pass@1",
            "mbpp": "pass@1",
            "code_search_net_java": "binary_label",
            "tl_code_sum": "binary_label",
        }

        if dataset == "advglue++":
            if cluster_method == "Grid":
                eval_folder_path = "{}/{}/{}_{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                    grid_history_dependency_num,
                )
            else:
                eval_folder_path = "{}/{}/{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                )
        else:
            if cluster_method == "Grid":
                eval_folder_path = "{}/{}/{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    grid_history_dependency_num,
                )
            else:
                eval_folder_path = "{}/{}/{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                )
        eval_folder_path = result_eval_path + "/" + eval_folder_path
        self.eval_folder_path = eval_folder_path
        self.train_instances, self.val_instances, self.test_instances = load_lists(
            eval_folder_path
        )

        self.train_transition_matrix, self.train_transition_probs = None, None

        self.train_traces = [i["state_trace"] for i in self.train_instances]
        self.val_traces = (
            [i["state_trace"] for i in self.val_instances] if self.val_instances else []
        )
        self.test_traces = [i["state_trace"] for i in self.test_instances]
        
        print("train traces length = {}".format(len(self.train_traces)))
        print("val traces length = {}".format(len(self.val_traces)))
        print("test traces length = {}".format(len(self.test_traces)))

        # if dataset != "truthful_qa":
            # print("first 5 val traces: ")
            # for i in range(5):
            #     print(self.val_traces[i], self.val_instances[i]["output"])
            # print("first 5 test traces: ")
            # for i in range(5):
            #     print(self.test_traces[i], self.test_instances[i]["output"])

        if dataset in groundtruths_key_dataset_map:
            key = groundtruths_key_dataset_map[dataset]
        else:
            print("illegal dataset")
            exit(1)

        self.train_groundtruths = [i[key] for i in self.train_instances]
        self.val_groundtruths = (
            [i[key] for i in self.val_instances] if self.val_instances else []
        )
        self.test_groundtruths = [i[key] for i in self.test_instances]

        ####### Analyze the length distribution ##############
        print("Analyze the length distribution...")

        length_set = []
        for one_trace in self.train_traces:
            length_set.append(len(one_trace))

        print(
            "in train_traces, max={},min={},median={},mean={}".format(
                np.max(length_set),
                np.min(length_set),
                np.median(length_set),
                np.mean(length_set),
            )
        )

        length_set = []
        for one_trace in self.val_traces:
            length_set.append(len(one_trace))
        print(
            "in val_traces, max={},min={},median={},mean={}".format(
                np.max(length_set),
                np.min(length_set),
                np.median(length_set),
                np.mean(length_set),
            )
            if self.val_instances
            else "no val set"
        )

        length_set = []
        for one_trace in self.test_traces:
            length_set.append(len(one_trace))
        print(
            "in test_traces, max={},min={},median={},mean={}".format(
                np.max(length_set),
                np.min(length_set),
                np.median(length_set),
                np.mean(length_set),
            )
        )
        self._get_train_transition_matrix()

        self._get_train_transition_probs()

    def eval_llm_performance_on_dataset_task(self, task):
        """
        Evaluate the performance of the LLM (Language Logit Model) on a specified dataset task.
        
        This method evaluates the accuracy of the model's outputs on various tasks such as "truthful_qa", "sst2", etc.
        It compares the model's outputs to ground truths and calculates metrics like accuracy. For certain tasks,
        it also evaluates the attack success rate.
        
        Parameters:
            task (str): The dataset task for which performance is to be evaluated. 
                        Possible values include "truthful_qa", "sst2", and others.
            
        Notes:
            - The method uses helper functions like `convert_output_to_label` to convert model outputs to label indices.
            - It calculates train, validation, and test accuracies based on the dataset task.
            - The method also prints the attack success rate for specific tasks.
            
        Raises:
            NotImplementedError: If an unknown task is provided.
        """
        def convert_output_to_label(output, dataset):
            answer_map = {
                "sst2": {"negative": 0, "positive": 1},
                "mnli": {"yes": 0, "maybe": 1, "no": 2},
                "mnli-mm": {"yes": 0, "maybe": 1, "no": 2},
                "qnli": {"yes": 0, "no": 1},
                "qqp": {"yes": 1, "no": 0},
                "rte": {"yes": 0, "no": 1},
            }
            output = output.lower()
            present_words = [
                word for word in answer_map[dataset].keys() if word in output
            ]

            if len(present_words) == 1:
                return answer_map[dataset][present_words[0]]
            else:
                return -1

        if task == "truthful_qa":
            train_output = [i["binary_label"] for i in self.train_instances]
            val_output = (
                [i["binary_label"] for i in self.val_instances]
                if self.val_instances
                else []
            )
            test_output = [i["binary_label"] for i in self.test_instances]

            train_groundtruths = [1 for _ in self.train_instances]
            val_groundtruths = (
                [1 for i in self.val_instances] if self.val_instances else []
            )
            test_groundtruths = [1 for _ in self.test_instances]

            output = train_output + val_output + test_output
            groundtruths = train_groundtruths + val_groundtruths + test_groundtruths
            print(
                "------------------ Accuracy = {} ------------------".format(
                    metrics.accuracy_score(groundtruths, output)
                )
            )
            return

        elif task == "sst2":
            train_output = [
                convert_output_to_label(i["output"], "sst2")
                for i in self.train_instances
            ]
            val_output = (
                [
                    convert_output_to_label(i["output"], "sst2")
                    for i in self.val_instances
                ]
                if self.val_instances
                else []
            )
            test_output = [
                convert_output_to_label(i["output"], "sst2")
                for i in self.test_instances
            ]

            train_groundtruths = [i["binary_label"] for i in self.train_instances]
            val_groundtruths = (
                [i["binary_label"] for i in self.val_instances]
                if self.val_instances
                else []
            )
            test_groundtruths = [i["binary_label"] for i in self.test_instances]

        elif task == "advglue++":
            train_output = []
            train_groundtruths = []
            train_acc_dict = {}
            for i in self.train_instances:
                output = convert_output_to_label(i["output"], i["adv_dataset"])
                train_output.append(output)
                train_groundtruths.append(i["binary_label"])

                if i["adv_dataset"] not in train_acc_dict:
                    train_acc_dict[i["adv_dataset"]] = (
                        1 if output == i["binary_label"] else 0
                    )
                else:
                    train_acc_dict[i["adv_dataset"]] += (
                        1 if output == i["binary_label"] else 0
                    )
            train_acc_dict = {
                k: v / len(self.train_instances) for k, v in train_acc_dict.items()
            }
            print(
                "------------------ Training Accuracy of {} ------------------".format(
                    task
                )
            )

            val_output = []
            val_groundtruths = []
            val_acc_dict = {}
            for i in self.val_instances:
                output = convert_output_to_label(i["output"], i["adv_dataset"])
                val_output.append(output)
                val_groundtruths.append(i["binary_label"])

                if i["adv_dataset"] not in val_acc_dict:
                    val_acc_dict[i["adv_dataset"]] = (
                        1 if output == i["binary_label"] else 0
                    )
                else:
                    val_acc_dict[i["adv_dataset"]] += (
                        1 if output == i["binary_label"] else 0
                    )
            val_acc_dict = {
                k: v / len(self.val_instances) for k, v in val_acc_dict.items()
            }
            print(
                "------------------ Validation Accuracy of {} ------------------".format(
                    task
                )
            )

            test_output = []
            test_groundtruths = []
            test_acc_dict = {}
            for i in self.test_instances:
                output = convert_output_to_label(i["output"], i["adv_dataset"])
                test_output.append(output)
                test_groundtruths.append(i["binary_label"])

                if i["adv_dataset"] not in test_acc_dict:
                    test_acc_dict[i["adv_dataset"]] = (
                        1 if output == i["binary_label"] else 0
                    )
                else:
                    test_acc_dict[i["adv_dataset"]] += (
                        1 if output == i["binary_label"] else 0
                    )
            test_acc_dict = {
                k: v / len(self.test_instances) for k, v in test_acc_dict.items()
            }
            print(
                "------------------ Testing Accuracy of {} ------------------".format(
                    task
                )
            )

            print(
                "------------------ Attack success rate of {} ------------------".format(
                    task
                )
            )
            # print(
            #     len(self.test_instances)
            #     / (len(self.val_instances) + len(self.train_instances))
            #     if self.test_instances[0]["is_attack_success"] == 1
            #     else (len(self.val_instances) + len(self.train_instances) - len(self.test_instances))
            #     / (len(self.val_instances) + len(self.train_instances))
            # )

        else:
            raise NotImplementedError("task {} not implemented".format(task))

        train_accuracy = metrics.accuracy_score(train_groundtruths, train_output)
        val_accuracy = (
            metrics.accuracy_score(val_groundtruths, val_output)
            if task != "truthful_qa"
            else None
        )
        test_accuracy = metrics.accuracy_score(test_groundtruths, test_output)

        print("================= Accuracy of {} ====================".format(task))
        print(
            "train_accuracy={}, val_accuracy={}, test_accuracy={}".format(
                train_accuracy, val_accuracy, test_accuracy
            )
        )

    def _get_train_transition_matrix(self):
        """
        Generate the transition matrix based on the training traces.
        
        This method constructs a transition matrix using the state traces from the training dataset. 
        The matrix represents the transitions between states and the frequency of each transition.
        
        Attributes:
            train_transition_matrix (dict): A dictionary where keys are starting states and values are 
                                        dictionaries representing next states and their transition counts.
                                        
        Notes:
            - The method iterates over state traces in the training dataset.
            - For each state in a trace, it checks the next state and updates the transition matrix accordingly.
            - The resulting matrix gives the frequency of transitions between every pair of states.
        """
        train_transition_matrix = {}

        for one_trace in self.train_traces:
            for j, start_state in enumerate(one_trace):
                if not (start_state in train_transition_matrix):
                    train_transition_matrix[start_state] = {}

                if j + 1 < len(one_trace):
                    next_state = one_trace[j + 1]
                    if next_state in train_transition_matrix[start_state]:
                        train_transition_matrix[start_state][next_state] += 1
                    else:
                        train_transition_matrix[start_state][next_state] = 1
                # else:
                #     # end state
                #     if -1 in train_transition_matrix[start_state]:
                #         train_transition_matrix[start_state][-1] += 1
                #     else:
                #         train_transition_matrix[start_state][-1] = 1
                        
        self.train_transition_matrix = train_transition_matrix

    def _get_train_transition_probs(self):
        """
        Compute the transition probabilities based on the training traces.
        
        This method calculates transition probabilities using the previously computed transition matrix 
        from the training dataset. It determines the likelihood of transitioning from one state to another.
        
        Attributes:
            train_transition_probs (dict): A dictionary where keys are starting states and values are 
                                        dictionaries representing next states and their transition probabilities.
                                        
        Notes:
            - If the transition matrix hasn't been computed yet, it calls the method to generate it.
            - The method iterates over the transition matrix and calculates probabilities by dividing the 
            frequency of each transition by the total transitions from the starting state.
            - The resulting dictionary gives the probability of transitions between every pair of states.
        """
        if self.train_transition_matrix is None:
            self.get_train_transition_matrix()

        train_transition_probs = {}
        for start_state in self.train_transition_matrix:
            count_all = 0.0
            if not (start_state in train_transition_probs):
                train_transition_probs[start_state] = {}

            for end_state in self.train_transition_matrix[start_state]:
                count_all += self.train_transition_matrix[start_state][end_state]

            for end_state in self.train_transition_matrix[start_state]:
                train_transition_probs[start_state][end_state] = (
                    self.train_transition_matrix[start_state][end_state] / count_all
                )

            # train_transition_probs[start_state][-1] = count_all

        self.train_transition_probs = train_transition_probs

    def compose_scores_with_groundtruths_pair(
        self, sentence_score_map, statistic_type="mean"
    ):
        """
        Compose prediction scores with ground truth labels into pairs for evaluation.
        
        This method pairs the computed prediction scores with the corresponding ground truth labels 
        based on the given statistic type (e.g., mean, sum, median, max, min).
        
        Parameters:
            sentence_score_map (dict): A dictionary where keys are ground truth labels and values 
                                    are lists of scores for corresponding sentences.
            statistic_type (str, optional): The type of statistic to be used for score computation. 
                                            Possible values include "mean", "sum", "median", "max", and "min". 
                                            Defaults to "mean".
            
        Returns:
            tuple: A tuple containing two lists:
                - y_pred (list): Computed prediction scores based on the specified statistic type.
                - y_groundtruth (list): Ground truth labels corresponding to the prediction scores.
            
        Notes:
            - The method iterates over the sentence_score_map and computes scores based on the specified statistic type.
            - For each entry in the map, it appends the computed score to the y_pred list and the ground truth 
            label to the y_groundtruth list.
            
        Raises:
            Exception: If an illegal statistic_type is provided.
        """
        y_pred = []
        y_groundtruth = []
        for label, positive_score_list in sentence_score_map:
            if len(positive_score_list) == 0:
                continue

            if label == 1:
                y_groundtruth.append(1)
            else:
                y_groundtruth.append(0)

            if len(positive_score_list) == 0:
                y_pred.append(1)
                continue
            else:
                if statistic_type == "mean":
                    pred_score = np.mean(positive_score_list)
                    y_pred.append(pred_score)
                elif statistic_type == "sum":
                    pred_score = np.sum(positive_score_list)
                    y_pred.append(pred_score)
                elif statistic_type == "median":
                    pred_score = np.median(positive_score_list)
                    y_pred.append(pred_score)
                elif statistic_type == "max":
                    pred_score = np.max(positive_score_list)
                    y_pred.append(pred_score)
                elif statistic_type == "min":
                    pred_score = np.min(positive_score_list)
                    y_pred.append(pred_score)
                else:
                    print("illeague statistic_type")
                    exit(1)

        return y_pred, y_groundtruth

    def calculate_auc_probs(self, sentence_scores):
        """
        Calculate the AUC-ROC (Area Under the Receiver Operating Characteristic Curve) for the given sentence scores.
        
        This method computes the AUC-ROC value based on the provided sentence scores and the corresponding 
        ground truth labels. It also evaluates the True Positive Rate (TPR) at various False Positive Rate (FPR) levels.
        
        Parameters:
            sentence_scores (dict): A dictionary where keys are ground truth labels and values 
                                    are lists of scores for corresponding sentences.
            
        Attributes:
            y_pred (list): Computed prediction scores.
            y_groundtruth (list): Ground truth labels corresponding to the prediction scores.
            
        Returns:
            tuple:
                - aucroc (float): The computed AUC-ROC value.
                - fpr (list): List of False Positive Rate values.
                - tpr (list): List of True Positive Rate values corresponding to the FPR values.
            
        Notes:
            - The method uses the `compose_scores_with_groundtruths_pair` to obtain predicted scores and ground truths.
            - It then uses the `roc_curve` method from the metrics module to calculate FPR and TPR.
            - The method also evaluates the TPR at specific FPR values (like 1e-1, 1e-2, etc.) using interpolation.
        """
        y_pred = []
        y_groundtruth = []

        y_pred, y_groundtruth = self.compose_scores_with_groundtruths_pair(
            sentence_scores
        )

        print(
            "y_pred length = {}, y_groundtruth length = {}".format(
                len(y_pred), len(y_groundtruth)
            )
        )
        self.y_pred = y_pred
        self.y_groundtruth = y_groundtruth

        fpr, tpr, thresholds = metrics.roc_curve(y_groundtruth, y_pred)
        aucroc = metrics.auc(fpr, tpr)

        roc_func = interpolate.interp1d(fpr, tpr)
        tpr_at_fpr_set_dist = {
            "1e-1": roc_func(1e-1),
            "1e-2": roc_func(1e-2),
            "1e-3": roc_func(1e-3),
            "1e-4": roc_func(1e-4),
            "1e-5": roc_func(1e-5),
            "1e-6": roc_func(1e-6),
        }
        print(tpr_at_fpr_set_dist)

        return aucroc, fpr, tpr


class HmmModel(ProbabilisticModel):
    def __init__(
        self,
        dataset,
        extract_block_idx,
        info_type,
        cluster_method,
        abstract_state,
        pca_dim,
        test_ratio,
        hmm_components_num,
        iter_num,
        is_attack_success,
        grid_history_dependency_num,
        result_eval_path,
    ):
        """
        Initialize the HmmModel class.
        
        Parameters:
            dataset (str): The name of the dataset being used.
            extract_block_idx (int): Index to determine which block to extract information from.
            info_type (str): Type of information to be extracted (e.g., 'hidden_states', 'attention').
            cluster_method (str): The clustering method used for state abstraction (e.g., 'Grid', 'GMM', 'KMeans').
            abstract_state (int): The number of abstract states.
            pca_dim (int): The number of dimensions for PCA reduction.
            test_ratio (float): Ratio of the dataset to be used for testing.
            hmm_components_num (int): The number of HMM components.
            iter_num (int): The number of iterations for training the HMM.
            is_attack_success (bool): Flag to determine if the attack was successful.
            grid_history_dependency_num (int): The number of history dependencies for the grid clustering method.
            
        Attributes:
            hmm_folder_path (str): Path to the folder containing the HMM model data.
            hmm_components_num (int): The number of HMM components.
            iter_num (int): The number of iterations for training the HMM.
            
        Notes:
            - The method initializes various instance attributes based on the provided arguments.
            - It constructs the path to the evaluation folder based on the dataset and other parameters.
        """
        super().__init__(
            dataset,
            extract_block_idx,
            info_type,
            cluster_method,
            abstract_state,
            pca_dim,
            test_ratio,
            is_attack_success,
            grid_history_dependency_num,
            result_eval_path,
        )

        if dataset == "advglue++":
            if cluster_method == "Grid":
                hmm_path = "hmm_{}_components_{}_{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    hmm_components_num,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                    grid_history_dependency_num,
                )
            else:
                hmm_path = "hmm_{}_components_{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    hmm_components_num,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                )
        else:
            if cluster_method == "Grid":
                hmm_path = "hmm_{}_components_{}_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    hmm_components_num,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    grid_history_dependency_num,
                )
            else:
                hmm_path = "hmm_{}_components_{}_{}_{}_{}_{}.pkl".format(
                    dataset,
                    extract_block_idx,
                    hmm_components_num,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                )
        hmm_folder_path = "{}/{}/{}/hmm".format(
            result_eval_path, dataset, extract_block_idx
        )
        if not os.path.exists(hmm_folder_path):
            os.makedirs(hmm_folder_path)
        hmm_files_path = hmm_folder_path + "/" + hmm_path
        self.hmm_files_path = hmm_files_path
        self.hmm_components_num = hmm_components_num
        self.iter_num = iter_num

    def _get_trained_hmm_models(
        self, data_points, n_component=150, n_iter=100
    ):
        """
        Train a Gaussian Hidden Markov Model (HMM) based on provided data points.
        
        This method uses the provided data points to train a Gaussian HMM. The method constructs
        training traces and then uses the GaussianHMM module to train the model.
        
        Parameters:
            data_points (list): A list of data points, where each point contains "step_by_step_analyzed_trace".
            n_component (int, optional): The number of components for the HMM. Defaults to 150.
            n_iter (int, optional): The number of iterations for training the HMM. Defaults to 100.
            
        Attributes:
            hmm_model (GaussianHMM): The trained Hidden Markov Model.
            
        Notes:
            - The method constructs training traces by concatenating "step_by_step_analyzed_trace" from each data point.
            - It uses the GaussianHMM module to train the model with the constructed traces.
            - The resulting model is stored in the `hmm_model` attribute.
        """
        hmm_training_trace_set = []
        length_set = []
        for i, one_point in enumerate(data_points):
            one_trace = one_point["step_by_step_analyzed_trace"]

            if len(length_set) > 0:
                hmm_training_trace_set = np.concatenate(
                    (hmm_training_trace_set, one_trace), axis=0
                )
                length_set.append(len(one_trace))
            else:
                hmm_training_trace_set = one_trace
                length_set.append(len(one_trace))

        hmm_model = hmm.GaussianHMM(
            n_components=n_component, 
            n_iter=n_iter, 
            covariance_type="full", 
            init_params='smtc', 
            random_state=42, 
        ).fit(
            hmm_training_trace_set.reshape((-1, 1)), length_set
        )
        self.hmm_model = hmm_model

    def _construct_hmmstate_transition_model(self, train_data_points):
        """
        Construct the transition model for HMM states based on training data points.
        
        This method computes a transition matrix for the HMM states using the provided training data points. 
        It determines the frequency of transitions between states and then calculates transition probabilities.
        
        Parameters:
            train_data_points (list): A list of data points, where each point contains "step_by_step_analyzed_trace".
            
        Attributes:
            train_transition_probs (dict): A dictionary representing the transition probabilities between HMM states.
            
        Returns:
            dict: A dictionary representing the transition probabilities between HMM states.
            
        Notes:
            - The method constructs a transition count matrix by iterating over the HMM state traces of each data point.
            - It uses the `decode` method of the trained HMM model to obtain HMM state traces from analyzed traces.
            - The resulting transition count matrix is then converted to a probability matrix.
        """
        hmmstate_transition_count_map = {}  # {start_state:{end_state: count}}

        for one_datapoint in train_data_points:
            trace = one_datapoint["step_by_step_analyzed_trace"]
            if len(trace) < 2:
                continue
            hmmstate_trace = self.hmm_model.decode([[x] for x in trace])[1].tolist()
            
            hmmsttate_trace_length = len(hmmstate_trace)

            for i, start_hmmstate in enumerate(hmmstate_trace):
                if not (start_hmmstate in hmmstate_transition_count_map):
                    hmmstate_transition_count_map[start_hmmstate] = {}

                if i + 1 < hmmsttate_trace_length:
                    end_state = hmmstate_trace[i + 1]

                    if end_state in hmmstate_transition_count_map[start_hmmstate]:
                        hmmstate_transition_count_map[start_hmmstate][end_state] += 1
                    else:
                        hmmstate_transition_count_map[start_hmmstate][end_state] = 1.0

        # transform the count to probability
        hmmstate_transition_probs_map = {}

        for start_hmmstate in hmmstate_transition_count_map:
            all_count = 0
            for end_hmmstate in hmmstate_transition_count_map[start_hmmstate]:
                all_count += hmmstate_transition_count_map[start_hmmstate][end_hmmstate]

            if not (start_hmmstate in hmmstate_transition_probs_map):
                hmmstate_transition_probs_map[start_hmmstate] = {}

            for end_hmmstate in hmmstate_transition_count_map[start_hmmstate]:
                hmmstate_transition_probs_map[start_hmmstate][end_hmmstate] = (
                    hmmstate_transition_count_map[start_hmmstate][end_hmmstate]
                    / all_count
                    if all_count > 0
                    else 0
                )
        self.train_transition_probs = hmmstate_transition_probs_map
        return hmmstate_transition_probs_map

    def construct_hmmstate_state_model(self, data_points):
        """
        Construct a model mapping HMM states to positive probabilities based on data points.
        
        This method computes the positive probabilities for each HMM state using the provided data points. 
        It determines the frequency of positive and negative labels for each state and calculates the state's positive probability.
        
        Parameters:
            data_points (list): A list of data points, where each point contains "step_by_step_analyzed_trace" and "label".
            
        Returns:
            dict: A dictionary mapping each HMM state to its positive probability.
            
        Notes:
            - The method constructs a statistics map by iterating over the HMM state traces of each data point.
            - It uses the `decode` method of the trained HMM model to obtain HMM state traces from analyzed traces.
            - The resulting statistics map is then used to calculate the positive probability for each state.
        """
        state_posterior_statics = {}

        for i, one_data in enumerate(data_points):
            one_trace = one_data["step_by_step_analyzed_trace"]
            label = one_data["label"]

            # shape of state_seq_with_posterior_prob = [num_of_seq, num_of_hmmstates]
            state_seq_with_posterior_prob = self.hmm_model.decode(
                [[x] for x in one_trace]
            )[1].tolist()

            # state_seq_with_posterior_prob = set(state_seq_with_posterior_prob)
            for _, state_id in enumerate(state_seq_with_posterior_prob):
                if not (state_id in state_posterior_statics):
                    state_posterior_statics[state_id] = {"pos": 0, "neg": 0}

                if label == 1:
                    state_posterior_statics[state_id]["pos"] += 1
                elif label == 0:
                    state_posterior_statics[state_id]["neg"] += 1

        num_of_hmmstates = len(state_posterior_statics)
        print("num_of_hmmstate = {}".format(num_of_hmmstates))

        state_positive_prob_map = {}
        for state in state_posterior_statics:
            state_positive_prob_map[state] = state_posterior_statics[state]["pos"] / (
                state_posterior_statics[state]["neg"]
                + state_posterior_statics[state]["pos"]
                + 1e-20
            )

        return state_positive_prob_map

    def get_sentence_scores_by_state_binding(
        self, traces, state_positive_prob_map, groundtruths
    ):
        sentence_positive_score_map = []
        for i, trace in enumerate(traces):
            label = groundtruths[i]
            hmmstate_trace = self.hmm_model.decode([[x] for x in trace])[1].tolist()
            state_sentence_scores = []

            for i, hmmstate in enumerate(hmmstate_trace):
                if hmmstate in state_positive_prob_map:
                    state_sentence_scores.append(state_positive_prob_map[hmmstate])
                else:
                    state_sentence_scores.append(0)

            if len(state_sentence_scores) == 0:
                continue

            sentence_positive_score_map.append((label, state_sentence_scores))
        return sentence_positive_score_map

    def get_sentence_scores_by_transition_binding(
        self, sentence_traces, groundtruths
    ):
        sentence_scores = []
        for i, one_trace in enumerate(sentence_traces):
            if len(one_trace) < 2:
                continue

            hmmstate_trace = self.hmm_model.predict([[x] for x in one_trace])
            hmmstate_trace_length = len(hmmstate_trace)
        
            one_set_score_list = []
            for j, start_hmmstate in enumerate(hmmstate_trace):
                if j + 1 < hmmstate_trace_length:
                    end_hmmstate = hmmstate_trace[j + 1]

                    if (
                        start_hmmstate in self.train_transition_probs
                        and end_hmmstate
                        in self.train_transition_probs[start_hmmstate]
                    ):
                        score = self.train_transition_probs[start_hmmstate][
                            end_hmmstate
                        ]
                        one_set_score_list.append(score)
                    else:
                        one_set_score_list.append(0.0)
            one_set_score_list = [x if x > 0 else 0 for x in one_set_score_list]
            sentence_scores.append((groundtruths[i], one_set_score_list))
        return sentence_scores
    
    def get_aucroc_by_transition_binding(self):
        train_data_points = [{} for _ in range(len(self.train_traces))]
        val_data_points = [{} for _ in range(len(self.val_traces))]
        test_data_points = [{} for _ in range(len(self.test_traces))]

        ####### extract training|test data [trace, label] pair
        for i, one_trace in enumerate(self.train_traces):
            train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
            train_data_points[i]["label"] = self.train_groundtruths[i]

        for i, one_trace in enumerate(self.test_traces):
            test_data_points[i]["step_by_step_analyzed_trace"] = one_trace
            test_data_points[i]["label"] = self.test_groundtruths[i]

        for i, one_trace in enumerate(self.val_traces):
            val_data_points[i]["step_by_step_analyzed_trace"] = one_trace
            val_data_points[i]["label"] = self.val_groundtruths[i]
        
        
        if os.path.exists(self.hmm_files_path):
            print("load hmm model from {}".format(self.hmm_files_path))
            with open(self.hmm_files_path, "rb") as f:
                self.hmm_model = pickle.load(f)
        else:
            print("start to train hmm model...")
            self._get_trained_hmm_models(
                train_data_points,
                n_component=self.hmm_components_num,
                n_iter=self.iter_num,
            )

            with open(self.hmm_files_path, "wb") as fw:
                pickle.dump(self.hmm_model, fw)
            print(
                "finish hmm modeling and saving in {}, start to analysis".format(
                    self.hmm_files_path
                )
            )

        # ######## construct hmm state transition models ########################################
        # hmmstate_transition_probs_map = self._construct_hmmstate_transition_model(
        #     train_data_points
        # )
        val_test_traces = self.val_traces + self.test_traces
        val_test_groundtruths = self.val_groundtruths + self.test_groundtruths

        ###################### generate the detection results#########################
        self.sentence_transition_positive_score_map = (
            self.get_sentence_scores_by_transition_binding(
                val_test_traces, val_test_groundtruths
            )
        )

        aucroc_score, fpr, tpr = self.calculate_auc_probs(
            self.sentence_transition_positive_score_map
        )

        print(
            "------------------ HMM Transition Binding AUCROC: {} ------------------".format(
                aucroc_score
            )
        )
        return aucroc_score, fpr, tpr

    def get_aucroc_by_state_binding(self):
        def all_elements_are_same(trace):
            return all(element == trace[0] for element in trace)

        train_data_points = []
        for i, one_trace in enumerate(self.train_traces):
            if not all_elements_are_same(one_trace):
                train_data_point = {
                    "step_by_step_analyzed_trace": one_trace,
                    "label": self.train_groundtruths[i]
                }
                train_data_points.append(train_data_point)

        test_data_points = []
        for i, one_trace in enumerate(self.test_traces):
            if not all_elements_are_same(one_trace):
                test_data_point = {
                    "step_by_step_analyzed_trace": one_trace,
                    "label": self.test_groundtruths[i]
                }
                test_data_points.append(test_data_point)

        val_data_points = []
        for i, one_trace in enumerate(self.val_traces):
            if not all_elements_are_same(one_trace):
                val_data_point = {
                    "step_by_step_analyzed_trace": one_trace,
                    "label": self.val_groundtruths[i]
                }
                val_data_points.append(val_data_point)


        if os.path.exists(self.hmm_files_path):
            print("load hmm model from {}".format(self.hmm_files_path))
            with open(self.hmm_files_path, "rb") as f:
                self.hmm_model = pickle.load(f)
        else:
            print("start to train hmm model...")
            self._get_trained_hmm_models(
                train_data_points,
                n_component=self.hmm_components_num,
                n_iter=self.iter_num,
            )

            with open(self.hmm_files_path, "wb") as fw:
                pickle.dump(self.hmm_model, fw)
            print(
                "finish hmm modeling and saving in {}, start to analysis".format(
                    self.hmm_files_path
                )
            )
        

        ######## construct hmm state models ########################################
        self.state_positive_prob_map = self.construct_hmmstate_state_model(
            train_data_points
        )

        val_test_traces = self.val_traces + self.test_traces
        val_test_groundtruths = self.val_groundtruths + self.test_groundtruths

        self.sentence_state_positive_score_map = (
            self.get_sentence_scores_by_state_binding(
                val_test_traces, self.state_positive_prob_map, val_test_groundtruths
            )
        )

        ###################### prediction ##############################
        aucroc_score, fpr, tpr = self.calculate_auc_probs(
            self.sentence_state_positive_score_map
        )

        print(
            "------------------ HMM State Binding AUCROC: {} ------------------".format(
                aucroc_score
            )
        )
        return aucroc_score, fpr, tpr


class DtmcModel(ProbabilisticModel):
    def __init__(
        self,
        dataset,
        extract_block_idx,
        info_type,
        cluster_method,
        abstract_state,
        pca_dim,
        test_ratio,
        is_attack_success,
        grid_history_dependency_num,
        result_eval_path,
    ):
        super().__init__(
            dataset,
            extract_block_idx,
            info_type,
            cluster_method,
            abstract_state,
            pca_dim,
            test_ratio,
            is_attack_success,
            grid_history_dependency_num,
            result_eval_path,
        )

    def construct_dtmc_state_model(self, data_points):
        state_posterior_statics = {}

        for one_data in data_points:
            one_trace = one_data["step_by_step_analyzed_trace"]
            label = one_data["label"]

            for state_id in one_trace:
                if not (state_id in state_posterior_statics):
                    state_posterior_statics[state_id] = {"pos": 0, "neg": 0}

                if label == 1:
                    state_posterior_statics[state_id]["pos"] += 1
                elif label == 0:
                    state_posterior_statics[state_id]["neg"] += 1

        state_positive_prob_map = {}
        for state in state_posterior_statics:
            state_positive_prob_map[state] = state_posterior_statics[state]["pos"] / (
                state_posterior_statics[state]["neg"]
                + state_posterior_statics[state]["pos"]
                + 1e-20
            )

        return state_positive_prob_map
    
    def get_semantic_state_model(self):
        instances = self.train_instances
        state_semantics = {}
        for instance in instances:
            one_trace = instance["state_trace"]
            truth_prob = instance["truth_prob"]
            for state_id in one_trace:
                if state_id not in state_semantics:
                    state_semantics[state_id] = [truth_prob]
                else:
                    state_semantics[state_id].append(truth_prob)
        
        state_semantics = {k: round(np.mean(v)*100) for k, v in state_semantics.items()}
        return state_semantics

    def get_sentence_scores_by_state_binding(
        self, sentence_traces, state_positive_prob_map, groundtruths
    ):
        sentence_positive_score = []
        for i, sentence in enumerate(sentence_traces):
            # Map the sentence tokens to their fake probabilities
            sentence_probs = []
            for token in sentence:
                if token not in state_positive_prob_map:
                    sentence_probs.append(0.0)
                else:
                    sentence_probs.append(state_positive_prob_map[token])

            # Calculate the mean fake probability for the sentence
            # sentence_probs = [1 - prob for prob in sentence_probs]
            # Classify the sentence as fake if mean_prob > 0.5, true otherwise
            sentence_positive_score.append((groundtruths[i], sentence_probs))
        return sentence_positive_score

    def get_sentence_scores_by_transition_binding(self, sentence_traces, groundtruths):
        sentence_scores = []
        for i, one_trace in enumerate(sentence_traces):
            if len(one_trace) < 2:
                continue

            one_set_score_list = []
            for j, start_state in enumerate(one_trace):
                if j + 1 < len(one_trace):
                    end_state = one_trace[j + 1]
                if (start_state in self.train_transition_probs) and (
                    end_state in self.train_transition_probs[start_state]
                ):
                    score = self.train_transition_probs[start_state][end_state]
                    one_set_score_list.append(score)
                else:
                    one_set_score_list.append(0.0)

            # one_set_score_list = [-np.log(score) if score > 0 else 0 for score in one_set_score_list]
            one_set_score_list = [x if x > 0 else 0 for x in one_set_score_list]
            sentence_scores.append((groundtruths[i], one_set_score_list))
        return sentence_scores

    def get_aucroc_by_transition_binding(self):
        ####### Analyze the test sentence_test_scores ##############
        val_test_traces = self.val_traces + self.test_traces
        val_test_groundtruths = self.val_groundtruths + self.test_groundtruths

        self.sentence_transition_positive_score_map = (
            self.get_sentence_scores_by_transition_binding(
                val_test_traces, val_test_groundtruths
            )
        )

        ###################### prediction ##############################
        aucroc_score, fpr, tpr = self.calculate_auc_probs(
            self.sentence_transition_positive_score_map
        )

        print(
            "------------------ DTMC Transition Binding AUCROC: {} ------------------".format(
                aucroc_score
            )
        )

        return aucroc_score, fpr, tpr

    def get_aucroc_by_state_binding(self):
        train_data_points = [{} for _ in range(len(self.train_traces))]
        ####### extract training|test data [trace, label] pair
        for i, one_trace in enumerate(self.train_traces):
            train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
            train_data_points[i]["label"] = self.train_groundtruths[i]

        self.state_positive_prob_map = self.construct_dtmc_state_model(
            train_data_points
        )
        ####### Analyze the test sentence_test_scores ##############
        val_test_traces = self.val_traces + self.test_traces
        val_test_groundtruths = self.val_groundtruths + self.test_groundtruths

        self.sentence_state_positive_score_map = (
            self.get_sentence_scores_by_state_binding(
                val_test_traces, self.state_positive_prob_map, val_test_groundtruths
            )
        )

        ###################### prediction ##############################
        aucroc_score, fpr, tpr = self.calculate_auc_probs(
            self.sentence_state_positive_score_map
        )

        print(
            "------------------ DTMC State Binding AUCROC: {} ------------------".format(
                aucroc_score
            )
        )

        return aucroc_score, fpr, tpr
