from luna.utils.activation_utils import get_llama_activations_bau, get_llama_loss, get_llama_probs
from luna.utils.prompter import Prompter
from luna.utils.llama import LlamaForCausalLM
from transformers import AutoTokenizer, AutoModelForCausalLM

import argparse
import os
import torch
from datasets import load_dataset
from tqdm import tqdm
import numpy as np
import joblib
import logging
import json
import pandas as pd

system_prompt = "You are a helpful, respectful and honest assistant with a deep knowledge of natural language processing. Always answer as helpfully as possible. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n"

def truthful_qa_inference(
    tokenizer,
    model,
    data_dict,
    device,
    max_new_tokens,
    result_save_path, 
    dataset,
    model_name
):
    max_new_tokens_num=100,
    layer_file_path_dict = {}
    for layer in range(32):
        dataset_folder = "{}/{}/{}".format(
            result_save_path, dataset, layer
        )
        if not os.path.exists(dataset_folder):
            os.makedirs(dataset_folder)

        file_path = "{}/{}/{}/{}_layer.joblib".format(
            result_save_path, dataset, layer, model_name
        )
        
        # Check if file exists
        if os.path.isfile(file_path):
            # If it exists, delete it
            os.remove(file_path)
            print(f"File {file_path} has been deleted.")

        fw = open(file_path, "ab+")
        print("File {} has been created.".format(file_path))
        layer_file_path_dict[layer] = fw
    
    for one_question in tqdm(data_dict):
        prompt = system_prompt + "Q: {}".format(one_question["question"])

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

        total_num_layers = len(current_hidden_states[0]) - 1

        len_question_tokens = len(question_tokens[0])
        generated_tokens = generated_tokens.sequences[0][len_question_tokens:]

        generated_text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        print("Generated text: {}".format(generated_text))

        question_tokens = question_tokens[0].tolist()
        
        step_by_step_head_wise_activations = []
        step_by_step_layer_wise_activations = []

        layer_wise_activations_dict = {}
        head_wise_activations_dict = {}
        for layer in range(total_num_layers):
            layer_wise_activations_dict[layer] = []
            head_wise_activations_dict[layer] = []

        for one_generated_token in generated_tokens.tolist():
            question_tokens.append(one_generated_token)

            # layer_wise_activations.shape = [num_blocks, num_tokens, hidden_size]
            # head_wise_activation.shape = [num_blocks, num_tokens, head_dim * num_of_head]
            (
                layer_wise_activations,
                head_wise_activations,
                _,
            ) = get_llama_activations_bau(
                model, torch.as_tensor([question_tokens]), device
            )
            # step_by_step_head_wise_activations.append(
            #     head_wise_activations[:, -1, :]
            # )
            # step_by_step_layer_wise_activations.append(
            #     layer_wise_activations[:, -1, :]
            # )
            for layer in range(total_num_layers):
                layer_wise_activations_dict[layer].append(layer_wise_activations[layer, -1, :])
                head_wise_activations_dict[layer].append(head_wise_activations[layer, -1, :])

        
        # print("head_wise_hidden_states.shape: ", len(step_by_step_head_wise_activations), step_by_step_head_wise_activations[0].shape)
        # print("layer_wise_hidden_states.shape: ", len(step_by_step_layer_wise_activations), step_by_step_layer_wise_activations[0].shape)

        for layer in range(total_num_layers):
            fw = layer_file_path_dict[layer]
            data_point = {
                "Q": one_question["question"],
                "A": generated_text,
                "hidden_states": layer_wise_activations_dict[layer],
                "attention_block_id": layer,
                "hidden_states_block_id": layer,
                "step_by_step_attention_heads": head_wise_activations_dict[layer],
                "original_data_record": one_question,
            }

            joblib.dump(data_point, fw)


def main():
    """
    Specify dataset name as the first command line argument. Current options are
    "truthful_qa", "advglue++", "sst2". Gets activations for all prompts in the
    validation set for the specified dataset on the last token for llama-7B.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="alpaca_7B")
    parser.add_argument("--dataset_name", type=str, default="truthful_qa")
    parser.add_argument("--result_save_path", type=str, default="outputs")
    parser.add_argument("--extract_attention_block_idx", type=int, default=0)
    parser.add_argument(
        "--hidden_states_block_idx", type=str, default="31", help="example: 0_15_31"
    )
    parser.add_argument("--max_new_tokens", type=int, default=50)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--cache_dir", type=str, required=True)
    args = parser.parse_args()

    HF_NAMES = {
        "llama_7B": "decapoda-research/llama-7b-hf",
        "llama2_7B": "meta-llama/Llama-2-7b-hf",
        "llama2_7B_chat": "meta-llama/Llama-2-7b-chat-hf",
        "llama2_13B_chat": "meta-llama/Llama-2-13b-chat-hf",
        "alpaca_7B": "circulus/alpaca-7b",
        "vicuna_7B": "AlekseyKorshuk/vicuna-7b",
    }

    model_name = args.model_name
    MODEL = HF_NAMES[model_name]

    tokenizer = AutoTokenizer.from_pretrained(MODEL, cache_dir=args.cache_dir)
    model = LlamaForCausalLM.from_pretrained(
        MODEL, low_cpu_mem_usage=True, torch_dtype=torch.float16, device_map="auto", cache_dir=args.cache_dir
    )


    device = args.device
    device = "cuda"
    max_new_tokens = args.max_new_tokens
    result_save_path = args.result_save_path

    dataset = args.dataset_name

    dataset = args.dataset_name
    model_name = args.model_name

    prompter = Prompter()

    # ========= Load Dataset ========= #
    data_dict = None
    # ========= QA ========= #
    if dataset == "truthful_qa":
        data_dict = load_dataset("truthful_qa", "generation")["validation"]
        truthful_qa_inference(
            tokenizer,
            model,
            data_dict,
            device,
            max_new_tokens,
            result_save_path,
            dataset,
            model_name
        )
    else:
        raise NotImplementedError


if __name__ == "__main__":
    main()
