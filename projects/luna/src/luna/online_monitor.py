from luna.state_abstraction_utils import AbstractStateExtraction
from luna.probabilistic_abstraction_model import (
    HmmModel,
    DtmcModel,
)
from luna.utils.prompter import Prompter
from luna.utils.ErrorWithReturn import ErrorWithReturn
import time
import numpy as np
import torch
# from transformers import AutoTokenizer, AutoModelForCausalLM
from luna.utils.llama import LLaMAForCausalLM, LLaMATokenizer
import pickle
import os
import luna.data_loader as data_loader
from sklearn.decomposition import PCA
from luna.abstraction_model import GMM, KMeans, RegularGrid
from luna.utils.probabilistic_model_checking import runtime_pmc
from tqdm import tqdm
from sklearn import metrics
import json

# ANSI escape codes for colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Function to print with color
def print_color(text, color):
    print(color + text + Colors.ENDC)


class OnlineMonitor:
    def __init__(
        self,
        abs_args,
        prob_args,
        train_instances=None,
        val_instances=None,
        test_instances=None,
    ):
        self.abs_args = abs_args
        self.prob_args = prob_args
        result_eval_path = "{}/eval/{}".format(abs_args.result_save_path, abs_args.llm_name) 
        abs_args.result_eval_path = result_eval_path
        self.abstract_utils = AbstractStateExtraction(
            abs_args, train_instances, val_instances, test_instances
        )
        self.dataset = prob_args.dataset
        
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
        if self.dataset == "truthful_qa":
            (
                self.dtmc_state_aucroc,
                self.dtmc_state_fpr,
                self.dtmc_state_tpr,
            ) = self.dtmc_model.get_aucroc_by_state_binding()
        else:
            (
                self.dtmc_transition_aucroc,
                self.dtmc_transition_fpr,
                self.dtmc_transition_tpr,
            ) = self.dtmc_model.get_aucroc_by_transition_binding()

        if prob_args.model_type == "DTMC":
            self.prob_model = self.dtmc_model
            self.test_abstract_traces = self.dtmc_model.test_traces
            self.val_abstract_traces = self.dtmc_model.val_traces
            self.train_abstract_traces = self.dtmc_model.train_traces

            train_data_points = [{} for _ in range(len(self.train_abstract_traces))]
            for i, one_trace in enumerate(self.train_abstract_traces):
                train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
                train_data_points[i]["label"] = self.dtmc_model.train_groundtruths[i]
            self.state_positive_prob_map = self.dtmc_model.construct_dtmc_state_model(
                train_data_points
            )

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
            (
                self.hmm_transition_aucroc,
                self.hmm_transition_fpr,
                self.hmm_transition_tpr,
            ) = self.hmm_model.get_aucroc_by_transition_binding()

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
            train_data_points = [{} for _ in range(len(self.train_abstract_traces))]
            for i, one_trace in enumerate(self.train_abstract_traces):
                train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
                train_data_points[i]["label"] = self.hmm_model.train_groundtruths[i]
            self.state_positive_prob_map = self.hmm_model.construct_hmmstate_state_model(
                train_data_points
            )
        else:
            raise NotImplementedError("Unknown model type!")


    def _parse_hidden_states(self, hidden_states, layer_indices=None):
        # trim the output of the embedding layer
        hidden_states = tuple(token[1:] for token in hidden_states)
        print(len(hidden_states), len(hidden_states[0]), hidden_states[0][0].shape)
        instance_result = None
        for i in range(len(hidden_states)):
            # traverse each token
            last_token_per_layer = None

            # For each tensor in the nested structure,
            # get the last element along the real token dimension
            for j in range(len(hidden_states[i])):
                if j not in layer_indices:
                    continue
                # traverse each layer
                # hidden_states[i][j].shape = torch.Size([1, 73, 4096])
                if last_token_per_layer is None:
                    last_token_per_layer = (
                        hidden_states[i][j][:, -1, :].detach().cpu().numpy()
                    )

                else:
                    last_token_per_layer = np.concatenate(
                        (
                            last_token_per_layer,
                            hidden_states[i][j][:, -1, :].detach().cpu().numpy(),
                        ),
                        axis=1,
                    )

            if instance_result is None:
                instance_result = last_token_per_layer
            else:
                instance_result = np.concatenate(
                    (instance_result, last_token_per_layer), axis=0
                )
            print("instance shape", instance_result.shape)
        return instance_result

    def _inference(
        self,
        input_text,
        tokenizer,
        model,
        device,
        monitor_threshold,
        hidden_states_block_idx_list,
    ):
        
        if self.dataset == "truthful_qa":
            prompt_text = "Q: {}".format(input_text)
            new_tokens_num = 40
        else:
            template = None
            with open("dataset/{}/prompt.json".format(self.dataset), "r") as f:
                template = json.load(f)
            prompter = Prompter()
            if self.dataset == "sst2":
                prompt_text = prompter.generate_prompt(template["sst2"], input_text)
                new_tokens_num = 10
            elif self.dataset == "advglue++":
                # TODO: Ask user what sub dataset they want to use. Only support sst2 currently. 
                prompt_text = prompter.generate_prompt(template["sst2"], input_text)
                new_tokens_num = 10

        input_tokens = tokenizer.encode(prompt_text, return_tensors="pt").to(
            device
        )
        model.set_current_monitoring_token_index(0)
        model.set_monitor_threshold(monitor_threshold)
        try:
            generated_tokens = model.generate(
                input_tokens,
                # top_k=128,
                max_new_tokens=new_tokens_num,
                num_return_sequences=1,
                output_scores=True,
                output_hidden_states=True,
                output_attentions=True,
                return_dict_in_generate=True,
            )
        except ErrorWithReturn as e:
            return e.return_value
        
        # Get the hidden states
        current_hidden_states = generated_tokens.hidden_states
        hidden_states = self._parse_hidden_states(
            current_hidden_states, hidden_states_block_idx_list
        )

        len_question_tokens = len(input_tokens[0])
        generated_tokens = generated_tokens.sequences[0][len_question_tokens:]

        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        print("Generated text: {}".format(generated_text))

        input_tokens = input_tokens[0].tolist()

        data_point = {
            "is_risk_detected": False,
            "input": prompt_text,
            "output": generated_text,
            "hidden_states": hidden_states,
            "hidden_states_block_id": hidden_states_block_idx_list,
        }
        return data_point


    def perform_inference(self, input_text, monitor_threshold, cache_dir):
        print_color("Performing inference...", Colors.WARNING)

        HF_NAMES = {
            "llama_7B": "decapoda-research/llama-7b-hf",
            "llama2_7B": "meta-llama/Llama-2-7b-hf",
            "alpaca_7B": "circulus/alpaca-7b",
            "vicuna_7B": "AlekseyKorshuk/vicuna-7b",
        }
        MODEL = HF_NAMES[self.abs_args.llm_name]
        device = "cuda"
        # Here you would perform the actual inference and get the output

        tokenizer = LLaMATokenizer.from_pretrained(MODEL, cache_dir=cache_dir)
        model = LLaMAForCausalLM.from_pretrained(
            MODEL, low_cpu_mem_usage=True, torch_dtype=torch.float16, device_map="auto", cache_dir=cache_dir
        )

        model.set_online_monitor_permission(True)
        model.set_abstract_model(self.state_positive_prob_map)
        model.set_pca_model(self.abstract_utils.pca_model)
        model.set_partition_model(self.abstract_utils.cluster_model)

        output = self._inference(
            input_text,
            tokenizer,
            model,
            device,
            monitor_threshold,
            hidden_states_block_idx_list=[self.prob_args.extract_block_idx],
        )
        return output


    # Placeholder for the function to send output to the abstract model
    def send_output_to_abstract_model(output, abstract_model, pca_model, partition_model):
        print_color("Sending output to LUNA...", Colors.OKBLUE)
        
        pca_data = pca_model.transform(output)
        abstract_trace = partition_model.clustering.predict(pca_data)

        # Here you would process the output with the abstract model    
        probabilities = [abstract_model[s] for s in abstract_trace]
        sentence_probs = []
        

        # Calculate the mean fake probability for the sentence
        sentence_probs = [round(prob, 2) for prob in probabilities]
        pred_score = round(np.mean(sentence_probs), 2)
        return abstract_trace, probabilities, pred_score

    # Placeholder for the function to show the generated result
    def show_generated_result(abstract_trace, probabilities, final_score):
        print_color("Generated result:", Colors.BOLD)
        print_color(f"Abstract Trace: {abstract_trace}", Colors.OKGREEN)
        print_color(f"Probabilities: {probabilities}", Colors.OKGREEN)
        print_color(f"Final Score: {final_score}", Colors.OKGREEN)

    
    def dtmc_to_prism(
        self,
        prism_folder_path,
    ):
        semantic_dataset_dict = {
            "truthful_qa": "truth_probability",
            "sst2": "is_ood",
            "advglue++": "is_adversarial",
        }
        if not os.path.exists(prism_folder_path):
            os.makedirs(prism_folder_path)
        
        prism_file_path = "{}/{}_{}_{}_{}_{}_{}_{}.pkl".format(
            prism_folder_path,
            self.prob_args.info_type,
            self.prob_args.cluster_method,
            self.prob_args.abstract_state,
            self.prob_args.pca_dim,
            self.prob_args.test_ratio,
            self.prob_args.is_attack_success,
            self.prob_args.grid_history_dependency_num,
        )

        semantic_value_dict = self.prob_model.get_semantic_state_model()
        # Increment state numbers by 1 to free up state 0
        incremented_dtmc_dict = {
            start_state
            + 1: {end_state + 1: prob for end_state, prob in transitions.items()}
            for start_state, transitions in self.prob_model.train_transition_probs.items()
        }

        semantic_value_dict = {
            state + 1: semantic_value for state, semantic_value in semantic_value_dict.items()
        }

        # Find the maximum state number for the state range after incrementing
        max_state = max(incremented_dtmc_dict.keys())

        # Start writing the PRISM model file content
        prism_content = f"dtmc\n\nmodule {self.abs_args.llm_name}\n\n"

        # Add the state declarations
        prism_content += f"// local state\nstate : [0..{max_state}] init 0;\n"
        prism_content += f"{semantic_dataset_dict[self.dataset]} : [0..100] init 0;\n\n"

        # Add the initial transition from state 0 to state 1 with probability 1
        prism_content += "// Initial transition from state 0 to state 1\n"
        prism_content += (
            f"[] state=0 -> 1 : (state'=1) & ({semantic_dataset_dict[self.dataset]}'={semantic_value_dict[1]});\n"
        )

        # Sort the states in ascending order and iterate over each start state in the incremented DTMC dictionary
        for start_state in sorted(incremented_dtmc_dict.keys()):

            transitions = incremented_dtmc_dict[start_state]
            if start_state == 19:
                print(transitions)

            # Skip the initial state since it has been already handled
            if start_state == 0:
                continue

            # Start the transitions for this state
            transitions_str = (
                f"// Transitions from state {start_state}\n[] state={start_state} -> "
            )

            # Gather the transition probabilities and next states
            transition_parts = []
            for end_state, probability in sorted(transitions.items()):
                # Format each transition part
                transition_parts.append(
                    f"{probability} : (state'={end_state}) & ({semantic_dataset_dict[self.dataset]}'={semantic_value_dict[end_state]})"
                )

            # Concatenate transition parts with '+' and add to the transitions string
            transitions_str += " + ".join(transition_parts) + ";\n"

            # Add the transitions to the PRISM model content
            prism_content += transitions_str

        # End the module
        prism_content += "\nendmodule\n"

        # Write the content to the output file
        with open(prism_file_path, "w") as f:
            f.write(prism_content)
        return prism_file_path

    def model_checking(self, prism_file_path):

        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        # Load models and data outside the loop because they only need to be loaded once

        # print(prism_file_path)

        # print(train_groundtruths)

        # print(train_instances[0].keys())
            #   ['question'])


        # print(dtmc_model.keys())
        # print(len(train_abstract_traces))
        # print(train_groundtruths)

        #  temperary offline evaluation of runtime monitor

        pmc_results = []
        i = 0
        trial_num = 50
        selected_state_list = [0,1,2,3,4,5]
        trial_traces = self.train_abstract_traces[:trial_num]
        verified_time = 3  # verification step
        truthfulness_prob = 50
        fail_threshold = 0.85
        trial_train_groundtruths = self.prob_model.train_groundtruths[:trial_num]

        eval_start = time.time()
        for selected_state in selected_state_list:
            print(f"selected_state: {selected_state}")
            pmc_results = []

            for train_abstract_trace in tqdm(trial_traces, desc="Online Monitoring On Progress"):
                checked_state = train_abstract_trace[selected_state]
                pmc_result = runtime_pmc.probabilistic_model_checking(prism_file_path, checked_state, verified_time, truthfulness_prob, fail_threshold)
                pmc_results.append(pmc_result)
                i += 1
                if i == trial_num:
                    break
                # print(f"instance: #{i}: {pmc_result}")
                
            fpr, tpr, thresholds = metrics.roc_curve(trial_train_groundtruths, pmc_results)
            auc = metrics.auc(fpr, tpr)

            print(auc)

        eval_end = time.time()
        print("evaluation time: " + str(eval_end - eval_start))