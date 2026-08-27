#! /bin/sh
#SBATCH --gres=gpu:1
#SBATCH --nodelist=gorina9
#SBATCH --partition=gpuA100
#SBATCH --time=29:59:59
#SBATCH --job-name=prefix-tuning_llama7b_subject_finance
#SBATCH --output=prefix-tuning_llama7b_subject_finance.out

#conda init bash
uenv verbose cuda-11.4 cudnn-11.4-8.2.4
uenv miniconda-python39
conda activate base

python finetune.py \
  --base_model 'yahma/llama-7b-hf' \
  --data_path 'dataset/subject-finance-instruct-177k/train.json' \
  --output_dir './trained_models/llama7b_prefix-tuning_subject-finance-instruct' \
  --batch_size 36 \
  --micro_batch_size 8 \
  --num_epochs 2 \
  --learning_rate 3e-4 \
  --eval_step 360 \
  --save_step 360 \
  --cutoff_len 256 \
  --val_set_size 120 \
  --use_gradient_checkpointing \
  --adapter_name prefix-tuning
