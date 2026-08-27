import fire
import gradio as gr
import torch
import transformers
import os
import sys
sys.path.append(os.path.join(os.getcwd(), "peft/src/"))
from peft import PeftModel, get_peft_model
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer
import os

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

try:
    if torch.backends.mps.is_available():
        device = "mps"
except:  # noqa: E722
    pass


def main(
    load_8bit: bool = False,
    base_model: str = "",
    lora_weights: str = "tloen/alpaca-lora-7b",
    output_dir: str = "full_model", 
):
    
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='decapoda-research/llama-7b-hf'"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    tokenizer = LlamaTokenizer.from_pretrained(base_model)
    
    if device == "cuda":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            load_in_8bit=load_8bit,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True,
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            torch_dtype=torch.float16,
        )
    elif device == "mps":
        model = LlamaForCausalLM.from_pretrained(
            base_model,
            device_map={"": device},
            torch_dtype=torch.float16,
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            device_map={"": device},
            torch_dtype=torch.float16,
        )
    else:
        model = LlamaForCausalLM.from_pretrained(
            base_model, device_map={"": device}, low_cpu_mem_usage=True
        )
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            device_map={"": device},
        )

    print("save full model to disk")
    print("type of model = {}".format(type(model)))
    fullmodel = model.merge_and_unload(progressbar=True, safe_merge=True)
    fullmodel.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
if __name__ == "__main__":
    fire.Fire(main)
