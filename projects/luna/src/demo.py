import time
from luna.state_abstraction_utils import AbstractStateExtraction
from luna.probabilistic_abstraction_model import (
    HmmModel,
    DtmcModel,
)
from types import SimpleNamespace
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
# from luna.utils.llama import LLaMAForCausalLM, LLaMATokenizer
import pickle
import os
import luna.data_loader as data_loader
from sklearn.decomposition import PCA
from luna.abstraction_model import GMM, KMeans, RegularGrid
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

llm = "alpaca_7B_with_semantics"
dataset = "truthful_qa"
result_save_path = "../../../data/songda"
extract_block_idx = 31
info_type = "hidden_states"
abstraction_method = "KMeans"
model_type = "DTMC"
hmm_n_comp = 100
abstract_state_num = 400
pca_dim = 2048
grid_history_dependency_num = 1
HF_NAMES = {
    "llama_7B": "decapoda-research/llama-7b-hf",
    "llama2_7B": "meta-llama/Llama-2-7b-hf",
    "code_llama_7B_python": "codellama/CodeLlama-7b-Python-hf",
    "code_llama_7B_instruct": "codellama/CodeLlama-7b-Instruct-hf",
    "code_llama_13B_instruct": "codellama/CodeLlama-13b-Instruct-hf",
    "alpaca_7B": "circulus/alpaca-7b",
    "vicuna_7B": "AlekseyKorshuk/vicuna-7b",
}
MODEL = HF_NAMES["alpaca_7B"]
device = "cuda"
cache_dir = "../../../data/songda/model/"

dataset_folder_path = "{}/{}/{}".format(
    result_save_path, dataset, str(extract_block_idx)
)


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

def construct_dtmc_state_model(data_points):
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

# Placeholder for the function to load the abstract model
def load_abstract_model(pca_model, partition_model, train_instances):
    print_color("Loading abstract model...", Colors.HEADER)

    if os.path.exists("eval/demo/{}_{}_{}_{}_{}_dtmc_model.pkl".format(
        llm,
        dataset,
        extract_block_idx,
        pca_dim,
        abstraction_method
    )):
        with open("eval/demo/{}_{}_{}_{}_{}_dtmc_model.pkl".format(
            llm,
            dataset,
            extract_block_idx,
            pca_dim,
            abstraction_method
        ), "rb") as f:
            dtmc_model = pickle.load(f)
            return dtmc_model
    else:
        train_hidden_states = [i["hidden_states"] for i in train_instances]
        train_groundtruths = [i["binary_label"] for i in train_instances]
        np_train_hidden_states = np.concatenate(train_hidden_states, axis=0)
        pca_train_data = pca_model.transform(np_train_hidden_states)
        partition_data = partition_model.clustering.predict(pca_train_data)

        cluster_label_count = 0
        for instance in tqdm(train_instances, desc="Format train traces"):
            instance_state_trace = []
            for _ in instance["hidden_states"]:
                state_id = int(partition_data[cluster_label_count])
                instance_state_trace.append(state_id)
                cluster_label_count += 1
            instance["state_trace"] = instance_state_trace
            instance["hidden_states"] = None
            instance["step_by_step_attention_heads"] = None
            instance["step_by_step_attention_blocks"] = None
        
        train_abstract_traces = [i["state_trace"] for i in train_instances]

        train_data_points = [{} for _ in range(len(train_abstract_traces))]
        for i, one_trace in enumerate(train_abstract_traces):
            train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
            train_data_points[i]["label"] = train_groundtruths[i]

            
        state_positive_prob_map = construct_dtmc_state_model(
            train_data_points
        )

        # save dtmc model
        with open("eval/demo/{}_{}_{}_{}_{}_dtmc_model.pkl".format(
            llm,
            dataset,
            extract_block_idx,
            pca_dim,
            abstraction_method
        ), "wb") as f:
            pickle.dump(state_positive_prob_map, f)

        return state_positive_prob_map

# Placeholder for the function to get input for the demo
def get_demo_input():
    print_color("Please type in the input: ", Colors.OKCYAN)
    input_text = input()  # Replace with actual input retrieval if necessary
    return input_text


def perform_inference(input_text):
    print_color("Performing inference...", Colors.WARNING)

    def parse_hidden_states(hidden_states, layer_indices=None):
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
        return instance_result

    def truthful_qa_inference(
        tokenizer,
        model,
        device,
        hidden_states_block_idx_list,
    ):
        question_text = "You are a helpful, respectful and honest assistant with a deep knowledge of code and software design. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information. {}".format(input_text)

        question_tokens = tokenizer.encode(question_text, return_tensors="pt").to(
            device
        )
        generated_tokens = model.generate(
            question_tokens,
            max_new_tokens=100,
            top_k=10,
            do_sample=True,
            top_p=0.9,
            temperature=0.1,
            output_scores=True,
            output_hidden_states=True,
            output_attentions=True,
            return_dict_in_generate=True,
            pad_token_id=model.config.eos_token_id,
        )
        # Get the hidden states
        current_hidden_states = generated_tokens.hidden_states
        hidden_states = parse_hidden_states(
            current_hidden_states, hidden_states_block_idx_list
        )

        len_question_tokens = len(question_tokens[0])
        generated_tokens = generated_tokens.sequences[0][len_question_tokens:]

        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        print("Generated text: {}".format(generated_text))

        question_tokens = question_tokens[0].tolist()

        data_point = {
            "Q": question_text,
            "A": generated_text,
            "hidden_states": hidden_states,
            "hidden_states_block_id": hidden_states_block_idx_list,
        }
        return data_point

    # Here you would perform the actual inference and get the output
    # if llm == "llama2_7B" or llm == "code_llama_7B_python":
    tokenizer = AutoTokenizer.from_pretrained(MODEL, cache_dir=cache_dir)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, low_cpu_mem_usage=True, torch_dtype=torch.float16, device_map="auto", cache_dir=cache_dir
    )
    # else:
    #     tokenizer = LLaMATokenizer.from_pretrained(MODEL, cache_dir=cache_dir)
    #     model = LLaMAForCausalLM.from_pretrained(
    #         MODEL, low_cpu_mem_usage=True, torch_dtype=torch.float16, device_map="auto", cache_dir=cache_dir
    #     )
    output = truthful_qa_inference(
        tokenizer,
        model,
        device,
        hidden_states_block_idx_list=[extract_block_idx],
    )
    return output


def get_pca_partition_model(train_instances):
    # check if pca_model pklfile exists
    # if exists, load it
    # else, train it
    pca_model_path = "eval/demo/{}_{}_{}_{}_pca_model.pkl".format(
        llm,
        dataset,
        extract_block_idx,
        pca_dim,
    )
    partition_model_path = "eval/demo/{}_{}_{}_{}_{}_partition_model.pkl".format(
        llm,
        dataset,
        extract_block_idx,
        pca_dim,
        abstraction_method
    )
    if os.path.exists(pca_model_path) and os.path.exists(partition_model_path):
        with open(pca_model_path, "rb") as f:
            pca_model = pickle.load(f)
        with open(partition_model_path, "rb") as f:
            partition_model = pickle.load(f)
    else:
        train_hidden_states = [i["hidden_states"] for i in train_instances]
        np_train_hidden_states = np.concatenate(train_hidden_states, axis=0)
        pca_model = PCA(n_components=pca_dim)
        pca_model.fit(np_train_hidden_states)
        pca_train_data = pca_model.transform(np_train_hidden_states)
        if abstraction_method == "GMM":
            partition_model = GMM(abstract_state_num)
        elif abstraction_method == "KMeans":
            partition_model = KMeans(abstract_state_num)
        # elif abstraction_method == "Grid":
        #     abstraction_model = RegularGrid(abstract_state_num, grid_history_dependency_num)
        else:
            raise NotImplementedError("Unknown partition method!")
        partition_model.clustering.fit(pca_train_data)
        with open(pca_model_path, "wb") as f:
            pickle.dump(pca_model, f)
        with open(partition_model_path, "wb") as f:
            pickle.dump(partition_model, f)

    return pca_model, partition_model



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

# Main function to run the program
def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    # input_text = get_demo_input()
    input_text = '''
    Ouestion: Are you a bird?
    '''
    output = perform_inference(input_text)
    print(output)
    loader = data_loader.TqaDataLoader(dataset_folder_path, llm)
    train_instances, _, _ = loader.load_hidden_states()
    pca_model, partition_model = get_pca_partition_model(train_instances)
    dtmc_model = load_abstract_model(pca_model, partition_model, train_instances)
    abstract_trace, probabilities, score = send_output_to_abstract_model(output["hidden_states"], dtmc_model, pca_model, partition_model)
    show_generated_result(abstract_trace, probabilities, score)

# Run the main function
if __name__ == "__main__":
    main()
