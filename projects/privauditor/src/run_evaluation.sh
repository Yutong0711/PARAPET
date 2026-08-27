CUDA_VISIBLE_DEVICES=5 python evaluate.py \
    --model LLaMA-7B \
    --adapter LoRA \
    --dataset SVAMP \
    --base_model 'yahma/llama-7b-hf' \
    --lora_weights './trained_models/llama-lora'
