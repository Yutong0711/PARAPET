#!/bin/bash
#SBATCH --job-name=deepseek_v2_lite_base_Effibench
#SBATCH --output=/mnt/beegfs/work/zhu1/work/EffiLearner/slurm_output/result.%j.%N.txt
#SBATCH --error=/mnt/beegfs/work/zhu1/work/EffiLearner/slurm_output/error.%j.%N.txt
#SBATCH --mail-user=derui.zhu@tu-darmstadt.de
#SBATCH --time=40:00
#SBATCH --mem=256GB
#SBATCH --gres=gpu:1
#SBATCH --constraint="gpu_model:a100"

## activate the env
#conda activate ukp
## change directory
cd /mnt/beegfs/work/zhu1/work/EffiLearner/src

python initial_code_generation_example.py --checkpoint deepseek-ai/DeepSeek-Coder-V2-Lite-Base --dataset EffiBench


## setup the virtual environmentbeforehand! on the login node do it like:
## mkdir -p /mnt/beegfs/work/USERNAME/jupyter_test
## cd /mnt/beegfs/work/USERNAME/jupyter_test
## python3 -m venv venv
## source venv/bin/activate
## (venv) pip install --upgrade pip
## (venv) pip install jupyter

## actually activate the virtual environment
#source venv/bin/activate

## start jupyter server on compute node on port 11337 (use anything between 1024 and 65535)

## you can test if jupyter is running from slurm login by executing
## curl http://krusty:11337/login
## replace "krusty" with the compute node name where your jupyter is running, this example uses krust as CPU node.
## add GPUs to the SBATCH setion above as desired. dont forget to also change partitions, qos and account if needed
## setup the redirect proxy on slurm login as stated in the wiki, like
## redir -I peters-jupyter -l none :5067 krusty:11337
## access the jupyter on http://slurm.ukp.informatik.tu-darmstadt.de:5067

