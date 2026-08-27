CUDA_VISIBLE_DEVICES=5 python model_full_transformation.py \
    --base_model 'yahma/llama-7b-hf' \
    --lora_weights './trained_models/llama7b-text2sql' \
    --output_dir './trained_models/full_model'
