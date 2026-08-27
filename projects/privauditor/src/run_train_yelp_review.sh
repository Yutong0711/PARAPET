#! /bin/sh
#SBATCH --gres=gpu:1
#SBATCH --nodelist=gorina9
#SBATCH --partition=gpuA100
#SBATCH --time=29:59:59
#SBATCH --job-name=alpaca-lora-yelp_review
#SBATCH --output=llm_lora_alpaca_yelp_review.out

#conda init bash
uenv verbose cuda-11.4 cudnn-11.4-8.2.4
uenv miniconda-python39
conda activate base

python finetune.py \
  --base_model 'yahma/llama-7b-hf' \
  --data_path 'dataset/yelp_review_full/train.json' \
  --output_dir './trained_models/llama7b-lora-yelp_review' \
  --batch_size 64 \
  --micro_batch_size 32 \
  --num_epochs 1 \
  --learning_rate 3e-4 \
  --cutoff_len 256 \
  --val_set_size 120 \
  --use_gradient_checkpointing \
  --adapter_name lora
