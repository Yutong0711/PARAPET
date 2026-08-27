#! /bin/sh
#SBATCH --gres=gpu:1
#SBATCH --nodelist=gorina9
#SBATCH --partition=gpuA100
#SBATCH --time=29:59:59
#SBATCH --job-name=llama7b-lora-text2sql
#SBATCH --output=lora_llama7b_text2sql.out

#conda init bash
uenv verbose cuda-11.4 cudnn-11.4-8.2.4
uenv miniconda-python39
conda activate base

python finetune.py \
  --base_model 'yahma/llama-7b-hf' \
  --data_path 'dataset/syntatic_text_to_sql/train.json' \
  --output_dir './trained_models/llama7b-text2sql' \
  --batch_size 32 \
  --micro_batch_size 8 \
  --num_epochs 2 \
  --learning_rate 3e-4 \
  --eval_step 320 \
  --save_step 320 \
  --cutoff_len 256 \
  --val_set_size 120 \
  --use_gradient_checkpointing \
  --adapter_name lora
