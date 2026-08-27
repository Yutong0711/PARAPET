export MIMIR_CACHE_PATH="./cache"
export MIMIR_DATA_SOURCE="./data_source"
CUDA_VISIBLE_DEVICES=5,6 python run.py --config configs/mi.json
