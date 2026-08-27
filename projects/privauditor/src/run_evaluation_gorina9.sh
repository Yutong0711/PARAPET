#! /bin/sh
#SBATCH --gres=gpu:1
#SBATCH --nodelist=gorina9
#SBATCH --partition=gpuA100
#SBATCH --time=29:59:59
#SBATCH --job-name=llm_evaluation_SVAMP
#SBATCH --output=llm_evaluation_SVAMP.out

#conda init bash
uenv verbose cuda-11.4 cudnn-11.4-8.2.4
uenv miniconda-python39
conda activate base

python evaluate.py \
    --model LLaMA-7B \
    --adapter LoRA \
    --dataset SVAMP \
    --base_model 'yahma/llama-7b-hf' \
    --lora_weights './trained_models/llama-lora'
