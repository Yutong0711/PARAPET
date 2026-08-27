#!/bin/bash
export ROOT_DIR=#current_dir

ENCODER=$1

declare -A RETRIEVER

RETRIEVER["simcse"]=princeton-nlp/unsup-simcse-bert-base-uncased
RETRIEVER["simcse_sup"]=princeton-nlp/sup-simcse-bert-base-uncased
RETRIEVER["contriever"]=facebook/contriever
RETRIEVER["contriever-msmarco"]=facebook/contriever-msmarco
RETRIEVER["dpr"]=facebook/dpr-question_encoder-multiset-base
RETRIEVER["ance"]=castorini/ance-dpr-question-multi
RETRIEVER["tasb"]=sentence-transformers/msmarco-distilbert-base-tas-b
RETRIEVER["colbert"]=colbert-ir/colbertv2.0
RETRIEVER["gtr-base"]=sentence-transformers/gtr-t5-base
RETRIEVER["gtr-large"]=sentence-transformers/gtr-t5-large
RETRIEVER["e5-base"]=intfloat/e5-base-v2
RETRIEVER["e5-large"]=intfloat/e5-large-v2
RETRIEVER["qwen"]=Alibaba-NLP/gte-Qwen2-1.5B-instruct
RETRIEVER["qwen-7b"]=Alibaba-NLP/gte-Qwen2-7B-instruct
RETRIEVER["e5"]=intfloat/e5-mistral-7b-instruct
RETRIEVER["bge-base"]=BAAI/bge-base-en-v1.5
RETRIEVER["bge-large"]=BAAI/bge-large-en-v1.5
RETRIEVER["bge-m3"]=BAAI/bge-m3
RETRIEVER["unixcoder"]=microsoft/unixcoder-base
RETRIEVER["gte-base"]=Alibaba-NLP/gte-base-en-v1.5
RETRIEVER["gte-large"]=Alibaba-NLP/gte-base-en-v1.5
RETRIEVER["gritlm"]=GritLM/GritLM-7B
RETRIEVER["tart-dual"]=orionweller/tart-dual-contriever-msmarco
RETRIEVER["instructor-base"]=hkunlp/instructor-base
RETRIEVER["instructor-large"]=hkunlp/instructor-large
RETRIEVER["instructor-xl"]=hkunlp/instructor-xl
RETRIEVER["bm25s"]=bm25s
RETRIEVER["retromae"]=Shitao/RetroMAE

RETRIEVER["promptriever-llama2"]=samaya-ai/promptriever-llama2-7b-v1
RETRIEVER["promptriever-llama3"]=samaya-ai/promptriever-llama3.1-8b-v1
RETRIEVER["promptriever-llama3-instruct"]=samaya-ai/promptriever-llama3.1-8b-instruct-v1
RETRIEVER["promptriever-mistral"]=samaya-ai/promptriever-mistral-v0.1-7b-v1

RETRIEVER["text-embedding-ada-002"]=openai/text-embedding-ada-002
RETRIEVER["text-embedding-3-small"]=openai/text-embedding-3-small
RETRIEVER["text-embedding-3-large"]=openai/text-embedding-3-large

RETRIEVER["voyage-code-2"]=voyageai/voyage-code-2
RETRIEVER["voyage-code-3"]=voyageai/voyage-code-3

# pretrained LLM
RETRIEVER["local-repllama-llama31-8b-lora-64"]=local-repllama-llama31-8b-lora-64
RETRIEVER["local-repllama-llama32-3b-lora-256"]=local-repllama-llama32-3b-lora-256

RETRIEVER["local-repllama-llama31-8b-lora-64-quality"]=local-repllama-llama31-8b-lora-64-quality
RETRIEVER["local-repllama-llama32-3b-lora-256-quality"]=local-repllama-llama32-3b-lora-256-quality

# code related models
RETRIEVER["coderankembed"]=nomic-ai/CodeRankEmbed
RETRIEVER["codebert"]=microsoft/codebert-base
RETRIEVER["graphcodebert"]=microsoft/graphcodebert-base
RETRIEVER["codesage-small"]=codesage/codesage-small
RETRIEVER["codesage-base"]=codesage/codesage-base

ENCODER_MODEL="${RETRIEVER["$ENCODER"]}"
echo $ENCODER_MODEL

export PYTHONPATH=$ROOT_DIR/src:$PYTHONPATH

for TASK in SQLR2PreferenceRetrieval CodeNetBugPreferenceRetrieval CodeNetEfficiencyPreferenceRetrieval SaferCodePreferenceRetrieval CVEFixesPreferenceRetrieval Defects4JPreferenceRetrieval DeprecatedCodePreferenceRetrieval
do
  python $ROOT_DIR/src/evaluate_retriever.py \
    --model_name $ENCODER_MODEL \
    --task_names $TASK \
    --top_k 200
done