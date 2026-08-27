CUDA_VISIBLE_DEVICES=5 python model_full_transformation.py \
    --base_model 'yahma/llama-7b-hf' \
    --lora_weights './trained_models/llama7b_lora_subject-finance-instruct/checkpoint-5760' \
    --output_dir './trained_models/fullmodel_llama7b_lora_finance'
