from transformers import T5ForConditionalGeneration, AutoTokenizer,GPTNeoForCausalLM,AutoModelForCausalLM,AutoModel, AutoModelForSeq2SeqLM
import torch
import json
from tqdm import tqdm
import os
import argparse
from datasets import load_dataset


def construct_prompt_template(inputs,checkpoint,model,tokenizer):
    device = "cuda"

    tokenizer.pad_token = tokenizer.eos_token
    input_tokens = tokenizer.batch_encode_plus(
    inputs,
    padding=True,
    return_tensors="pt",

    ).to(model.device)
    for t in input_tokens:
        if torch.is_tensor(input_tokens[t]):
            input_tokens[t] = input_tokens[t].to(model.device)
    # input_tokens.pop("token_type_ids")
    try:
        sequences = model.generate(
        **input_tokens, max_new_tokens=512, do_sample=True
        )
        generated_texts = tokenizer.batch_decode(sequences, skip_special_tokens=True)
        for i in range(len(generated_texts)):
            if inputs[i] in generated_texts[i]:
                generated_texts[i] = generated_texts[i].replace(inputs[i], "")
    except:
        generated_texts = ["" for i in range(len(inputs))]

    return generated_texts


# Function to fetch completion
def fetch_completion(data_entry_lists, model,checkpoint,tokenizer):
    return_batchs = data_entry_lists
    inputs_batchs = []
    for data_entry in data_entry_lists:
        if data_entry["dataset"] == "EffiBench":
            test_case = data_entry["small_test_cases"]
            inputs_batchs.append(f"Please complete Python code based on the task description and test cases. # Task description:\n{data_entry['markdown_description']}\n{test_case}\n#Solution:\n")
        elif data_entry["dataset"] == "HumanEval":
            inputs_batchs.append(f"Please complete Python code based on the task description. # Task description:\n{data_entry['prompt']}\n#Solution:\n")
        elif data_entry["dataset"] == "MBPP":
            tests = "\n".join(data_entry["test_list"])
            inputs_batchs.append(f"Please complete Python code based on the task description and test cases. # Task description:\n{data_entry['prompt']}\n{tests}\n#Solution:\n")

    completion_lists = construct_prompt_template(inputs_batchs,checkpoint,model,tokenizer)
    for i in range(len(data_entry_lists)):
        data_entry_lists[i]["completion"] = completion_lists[i]

    return data_entry_lists


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--checkpoint", type=str, default="m-a-p/OpenCodeInterpreter-DS-33B", required=True)
    args.add_argument("--batch_size", type=int, default=16)
    args.add_argument("--dataset", type=str, required=True)
    args = args.parse_args()

    checkpoint = args.checkpoint
    batch_size = args.batch_size
    print("Checkpoint: ",checkpoint)

    if "/" in checkpoint:
        end_name = checkpoint.split("/")[-1]

    if args.dataset == "EffiBench":
        with open("../datasets/dataset.json", "r") as f:
            dataset = json.load(f)
    elif args.dataset == "HumanEval":
        dataset = load_dataset("evalplus/humanevalplus",split="test")
    elif args.dataset == "MBPP":
        dataset = load_dataset("evalplus/mbppplus",split="test")
    for i in range(len(dataset)):
        dataset[i]["dataset"] = args.dataset

    model = AutoModelForCausalLM.from_pretrained(checkpoint,device_map = "auto",trust_remote_code=True,torch_dtype=torch.float16)
    tokenizer = AutoTokenizer.from_pretrained(checkpoint,trust_remote_code=True)

    for i in tqdm(range(0,len(dataset),batch_size)):
        dataset[i:i+batch_size] = fetch_completion(dataset[i:i+batch_size],model,checkpoint,tokenizer)

    end_name = checkpoint.split("/")[-1]
    with open(f"../results/{args.dataset}_{end_name}.json", "w") as f:
        json.dump(dataset, f, indent=4)
