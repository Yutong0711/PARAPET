CUDA_VISIBLE_DEVICES=5 python model_full_transformation.py \
    --base_model 'yahma/llama-7b-hf' \
    --lora_weights './trained_models/llama7b_prefix-tuning_subject-finance-instruct' \
    --output_dir './trained_models/fullmodel_llama7b_prefix-tuning_finance'
