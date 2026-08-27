# from luna.utils.activation_utils import (
#     get_llama_activations_bau,
#     get_llama_loss,
#     get_llama_probs,
# )
# from luna.utils.prompter import Prompter
# from luna.utils.llama import LLaMAForCausalLM, LLaMATokenizer
from luna.utils.code_generation import human_eval, mbpp
from transformers import AutoTokenizer, AutoModelForCausalLM


import argparse
import os
import torch
from tqdm import tqdm
import numpy as np
import joblib
import logging
import jsonlines
import random


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
    print("instance_result.shape", instance_result.shape)
    return instance_result


def codegen_inference(
    dataset,
    fw,
    tokenizer,
    model,
    device,
    max_new_tokens,
    extract_attention_block_idx,
    hidden_states_block_idx_list,
):
    if dataset == "mbpp":
        task = mbpp.MBPP()
    elif dataset == "humaneval":
        task = human_eval.HumanEval()
    else:
        raise ValueError("Dataset {} not supported.".format(dataset))
    dataset = task.get_dataset()
    dataset_len = len(dataset)
    references = [task.get_reference(dataset[i]) for i in range(dataset_len)]
    for index in tqdm(range(dataset_len)):
        prompt = task.get_prompt(dataset[index])

        tokenizer.pad_token = tokenizer.eos_token
        encoded_input = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True).to(device)
        
        question_tokens = encoded_input['input_ids']
        attention_mask = encoded_input['attention_mask']
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
            attention_mask=attention_mask,
        )
        # Get the hidden states
        current_hidden_states = generated_tokens.hidden_states
        hidden_states = parse_hidden_states(
            current_hidden_states, hidden_states_block_idx_list
        )

        len_question_tokens = len(question_tokens[0])
        full_generated_tokens = generated_tokens.sequences[0]
        generated_tokens = generated_tokens.sequences[0][len_question_tokens:]

        full_generated_text = tokenizer.decode(
            full_generated_tokens, skip_special_tokens=True
        )
        output_generated_text = tokenizer.decode(
            generated_tokens, skip_special_tokens=True
        )

        question_tokens = question_tokens[0].tolist()

        # step_by_step_layer_wise_activations = []
        # step_by_step_head_wise_activations = []

        # for one_generated_token in generated_tokens.tolist():
        #     question_tokens.append(one_generated_token)

        #     # layer_wise_activations.shape = [num_blocks, num_tokens, hidden_size]
        #     # head_wise_activation.shape = [num_blocks, num_tokens, head_dim * num_of_head]
        #     (
        #         layer_wise_activations,
        #         head_wise_activations,
        #         _,
        #     ) = get_llama_activations_bau(
        #         model, torch.as_tensor([question_tokens]), device
        #     )

        #     step_by_step_layer_wise_activations.append(
        #         layer_wise_activations[extract_attention_block_idx + 1, -1, :]
        #     )
        #     step_by_step_head_wise_activations.append(
        #         head_wise_activations[extract_attention_block_idx, -1, :]
        #     )

        print("full_generated_text", full_generated_text)
        text_output = task.postprocess_generation(full_generated_text, index)
        print("text_output", text_output)

        print("references[index]", references[index])
        code_output = task.process_results([[text_output]], [references[index]])
        print("code_output", code_output)

        data_point = {
            "input": prompt,
            "output": text_output,
            "code_output": code_output,
            "hidden_states": hidden_states,
            "references": references[index],
            "attention_block_id": extract_attention_block_idx,
            "hidden_states_block_id": hidden_states_block_idx_list,
            # "step_by_step_attention_heads": step_by_step_head_wise_activations,
            # "step_by_step_attention_blocks": step_by_step_layer_wise_activations,
            "original_data_record": dataset[index],
        }

        joblib.dump(data_point, fw)


def generate_random_select_codesearchnet_data(
    train,
    test,
    number,
    insturction,
    input_insturction,
    output_insturction,
    output_path,
):
    print("Start generate random select codesearchnet data...")
    samples = []
    random.shuffle(train)
    random.shuffle(test)

    for idx in range(number):
        prompt = ""
        prompt += insturction
        prompt += input_insturction
        prompt += (
            " ".join(
                train[idx]["code_tokens"]
            ).strip()
            + "\n"
        )
        prompt += output_insturction
        prompt += "\n\n"
        samples.append(
            {"prompt": prompt, "label": " ".join(train[idx]["docstring_tokens"])}
        )
    
    for obj in test[:number]:
        prompt = ""
        prompt = prompt + insturction + input_insturction
        prompt += (
            " ".join(
                train[idx]["code_tokens"]
            ).strip()
            + "\n"
        )
        prompt += output_insturction
        samples.append(
            {"prompt": prompt, "label": " ".join(obj["docstring_tokens"])}
        )
    
    with jsonlines.open(
        os.path.join(output_path, "test_samples_and_random_train_samples_" + str(number) + ".jsonl"), "w"
    ) as f:
        f.write_all(samples)

    print("Finish generate random select codesearchnet data...")
    
    return samples


def code_summarization_inference(
    samples,
    fw,
    tokenizer,
    model,
    device,
    max_new_tokens,
    extract_attention_block_idx,
    hidden_states_block_idx_list,
):
    print("Start code summarization inference...")
    for index in tqdm(range(len(samples))):
        prompt = samples[index]["prompt"]

        # question_tokens = tokenizer.encode(prompt, return_tensors="pt").to(device)
        tokenizer.pad_token = tokenizer.eos_token
        encoded_input = tokenizer(prompt, return_tensors='pt', padding=True, truncation=True).to(device)
        
        question_tokens = encoded_input['input_ids']
        attention_mask = encoded_input['attention_mask']
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
            attention_mask=attention_mask,
        )
        # Get the hidden states
        current_hidden_states = generated_tokens.hidden_states
        hidden_states = parse_hidden_states(
            current_hidden_states, hidden_states_block_idx_list
        )

        len_input_tokens = len(question_tokens[0])
        generated_tokens = generated_tokens.sequences[0][len_input_tokens:]

        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        print("Generated text: {}".format(generated_text))

        data_point = {
            "input": prompt,
            "output": generated_text,
            "ground_truth": samples[index]["label"],
            "hidden_states": hidden_states,
            "hidden_states_block_id": hidden_states_block_idx_list,
            "original_data_record": samples[index],
        }

        joblib.dump(data_point, fw)
    print("Finish code summarization inference...")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--dataset_name", type=str, required=True)
    parser.add_argument("--result_save_path", type=str, required=True)
    parser.add_argument("--extract_attention_block_idx", type=int, default=0)
    parser.add_argument(
        "--hidden_states_block_idx", type=str, default="31", help="example: 0_15_31"
    )
    parser.add_argument("--max_new_tokens", type=int, default=50)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--cache_dir", type=str, required=True)
    args = parser.parse_args()

    HF_NAMES = {
        "codellama-7b-Python": "codellama/CodeLlama-7b-Python-hf",
        "codellama-7b-Instruct": "codellama/CodeLlama-7b-Instruct-hf",
        "codellama-13b-Instruct": "codellama/CodeLlama-13b-Instruct-hf",
        "codellama-13b-Python": "codellama/CodeLlama-13b-Python-hf",
    }

    os.environ["HF_ALLOW_CODE_EVAL"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    model_name = args.model_name
    MODEL = HF_NAMES[model_name]

    tokenizer = AutoTokenizer.from_pretrained(MODEL, cache_dir=args.cache_dir)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL,
        low_cpu_mem_usage=True,
        torch_dtype=torch.float16,
        device_map="auto",
        cache_dir=args.cache_dir,
    )

    device = args.device
    device = "cuda"
    max_new_tokens = args.max_new_tokens
    result_save_path = args.result_save_path
    extract_attention_block_idx = args.extract_attention_block_idx
    hidden_states_block_idx_str = args.hidden_states_block_idx

    dataset = args.dataset_name

    hidden_states_block_idx_list = [
        int(i) for i in args.hidden_states_block_idx.split("_")
    ]
    dataset = args.dataset_name
    model_name = args.model_name

    dataset_folder = "{}/{}/{}".format(
        result_save_path, dataset, hidden_states_block_idx_str
    )
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)

    logging.basicConfig(
        filename="logs/{}_{}.log".format(model_name, dataset), level=logging.INFO
    )
    file_path = "{}/{}/{}/{}.joblib".format(
        result_save_path, dataset, hidden_states_block_idx_str, model_name
    )

    # Check if file exists
    if os.path.isfile(file_path):
        # If it exists, delete it
        os.remove(file_path)
        print(f"File {file_path} has been deleted.")

    fw = open(file_path, "ab+")
    print("File {} has been created.".format(file_path))
    if dataset == "mbpp" or dataset == "humaneval":
        codegen_inference(
            dataset,
            fw,
            tokenizer,
            model,
            device,
            max_new_tokens,
            extract_attention_block_idx,
            hidden_states_block_idx_list,
        )
    elif dataset == "code_search_net_java" or dataset == "tl_code_sum":
        samples = []
        samples_file_path = f"{result_save_path}/{dataset}/random_samples_5000.jsonl"
        if os.path.exists(samples_file_path):
            with jsonlines.open(samples_file_path) as f:
                for i in f:
                    samples.append(i)
        else:
            # train = []
            # test = []
            # with jsonlines.open(
            #     f"{result_save_path}/{dataset}/java/train.jsonl"
            # ) as f:
            #     for i in f:
            #         train.append(i)
            # with jsonlines.open(
            #     f"{result_save_path}/{dataset}/java/test.jsonl"
            # ) as f:
            #     for i in f:
            #         test.append(i)

            # number = 2000
            # system_prompt = "You are a helpful, respectful and honest assistant with a deep knowledge of code and software design. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n"
            # insturction = (
            #     system_prompt + "Generate comment (summarization) for this code  \n"
            # )
            # input_insturction = " [input] "
            # output_insturction = " [output] "

            # samples = generate_random_select_codesearchnet_data(
            #     train,
            #     test,
            #     number,
            #     insturction,
            #     input_insturction,
            #     output_insturction,
            #     result_save_path,
            # )
            raise ValueError("File {} not exists.".format(samples_file_path))
        code_summarization_inference(
            samples,
            fw,
            tokenizer,
            model,
            device,
            max_new_tokens,
            extract_attention_block_idx,
            hidden_states_block_idx_list,
        )


if __name__ == "__main__":
    main()
