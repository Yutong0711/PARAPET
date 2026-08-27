import json
import os
import glob
import numpy as np


def calculate_memory_usage(dat_file_path):
    with open(dat_file_path, 'r') as file:
        prev_time = 0
        prev_mem_mb = 0
        mem_time_mb_s = 0
        next(file)
        for line in file:
            if "__main__." in line:
                continue
            parts = line.split()
            mem_in_mb = float(parts[1])
            timestamp = float(parts[2])
            if prev_time > 0:
                time_interval_s = timestamp - prev_time
                mem_time_mb_s += (prev_mem_mb + mem_in_mb) / 2 * time_interval_s
            prev_time = timestamp
            prev_mem_mb = mem_in_mb
        return mem_time_mb_s


def calculate_runtime(dat_file_path):
    with open(dat_file_path, 'r') as file:
        start_time = float("inf")
        end_time = float("-inf")
        next(file)
        for line in file:
            if "__main__." in line:
                continue
            parts = line.split()
            timestamp = float(parts[2])
            start_time = min(start_time, timestamp)
            end_time = max(end_time, timestamp)
        return max(end_time - start_time,0)

def report_max_memory_usage(dat_file_path):
    max_memory_usage = 0
    with open(dat_file_path, 'r') as file:
        next(file)
        for line in file:
            if "__main__." in line:
                continue
            parts = line.split()
            mem_in_mb = float(parts[1])
            max_memory_usage = max(max_memory_usage, mem_in_mb)
        return max_memory_usage

# model_list = ["m-a-p/OpenCodeInterpreter-DS-1.3B", "m-a-p/OpenCodeInterpreter-DS-6.7B", "m-a-p/OpenCodeInterpreter-DS-33B","deepseek-ai/deepseek-coder-1.3b-instruct","deepseek-ai/deepseek-coder-6.7b-instruct","deepseek-ai/deepseek-coder-33b-instruct","codellama/CodeLlama-7b-Instruct-hf","codellama/CodeLlama-13b-Instruct-hf","codellama/CodeLlama-34b-Instruct-hf","codellama/CodeLlama-70b-Instruct-hf","Xwin-LM/XwinCoder-7B","Xwin-LM/XwinCoder-13B","Xwin-LM/XwinCoder-34B","TheBloke/WizardCoder-Python-7B-V1.0-GPTQ","TheBloke/WizardCoder-Python-13B-V1.0-GPTQ","TheBloke/WizardCoder-Python-34B-V1.0-GPTQ","bigcode/starcoder2-3b","bigcode/starcoder2-7b","bigcode/starcoder2-15b"]
model_list = ["m-a-p/OpenCodeInterpreter-DS-1.3B", "m-a-p/OpenCodeInterpreter-DS-6.7B", "m-a-p/OpenCodeInterpreter-DS-33B",]
canonical_solution_directory = "./dat_results/humaneval_canonical_solution_timeout10"
canonical_solution_memory_usage = {}
canonical_solution_execution_time = {}
canonical_solution_max_memory_usage = {}
for dat_file in glob.glob(os.path.join(canonical_solution_directory, "*.dat")):
    try:
        problem_idx = os.path.basename(dat_file).split('.')[0]
        canonical_solution_memory_usage[int(problem_idx)] = calculate_memory_usage(dat_file)
        canonical_solution_execution_time[int(problem_idx)] = calculate_runtime(dat_file)
        canonical_solution_max_memory_usage[int(problem_idx)] = report_max_memory_usage(dat_file)
    except:
        pass


global_result = {}

for model in model_list:
    if "/" in model:
        model = model.split("/")[1]
    completion_memory_usage = {}
    execution_time = {}
    max_memory_usage = {}
    task_idx = {}
    dat_directory = f"./dat_results/humaneval_{model}_timeout10"
    for dat_file in glob.glob(os.path.join(dat_directory, "*.dat")):
        if "_5/" in dat_file:
            if not os.path.exists(dat_file.replace("_5/","/")):
                continue
        else:
            if not os.path.exists(dat_file.replace(f"./dat_results/humaneval_{model}_timeout10",f"./dat_results/humaneval_{model}_timeout10_5")):
                continue
        try:
            tmp_model = model
            if "_" in model:
                tmp_model = model.split("_")[0]
            problem_idx = os.path.basename(dat_file).split('.')[0]

            execution_time_result = calculate_runtime(dat_file)
            completion_memory_usage[int(problem_idx)] = calculate_memory_usage(dat_file)
            execution_time[int(problem_idx)] = calculate_runtime(dat_file)
            max_memory_usage[int(problem_idx)] = report_max_memory_usage(dat_file)
            task_idx[int(problem_idx)] = dat_file
        except Exception as e:
            # print(e)
            print(dat_file)
    global_result[model] = {"completion_memory_usage":completion_memory_usage,"execution_time":execution_time,"max_memory_usage":max_memory_usage,"task_idx":task_idx}

save_results = []

for model in global_result.keys():

    completion_memory_usage = global_result[model]["completion_memory_usage"]
    execution_time = global_result[model]["execution_time"]
    max_memory_usage = global_result[model]["max_memory_usage"]

    # report execution time
    total_execution_time = 0

    # report normalized execution time
    normalized_execution_time = 0

    # report max memory usage
    total_max_memory_usage = 0

    # report normalized max memory usage
    normalized_max_memory_usage = 0

    # report memory usage
    total_memory_usage = 0
    total_canonical_solution_max_memory_usage = 0
    total_canonical_solution_execution_time = 0
    total_canonical_solution_memory_usage = 0
    # report normalized memory usage
    normalized_memory_usage = 0
    total_codes = 0
    normalized_execution_time_list = []
    normalized_max_memory_usage_list = []
    normalized_memory_usage_list = []
    total_fast = 0

    for idx in completion_memory_usage.keys():
        total_memory_usage += completion_memory_usage[idx]
        total_execution_time += execution_time[idx]
        total_max_memory_usage += max_memory_usage[idx]
        total_canonical_solution_max_memory_usage+=canonical_solution_max_memory_usage[idx]
        total_canonical_solution_memory_usage+=canonical_solution_memory_usage[idx]
        total_canonical_solution_execution_time+=canonical_solution_execution_time[idx]

        normalized_execution_time += execution_time[idx]/canonical_solution_execution_time[idx]
        normalized_execution_time_list.append(execution_time[idx]/canonical_solution_execution_time[idx])

        normalized_max_memory_usage += max_memory_usage[idx]/canonical_solution_max_memory_usage[idx]
        normalized_max_memory_usage_list.append(max_memory_usage[idx]/canonical_solution_max_memory_usage[idx])

        normalized_memory_usage += completion_memory_usage[idx]/canonical_solution_memory_usage[idx]
        normalized_memory_usage_list.append(completion_memory_usage[idx]/canonical_solution_memory_usage[idx])

        total_codes+=1

    if len(normalized_execution_time_list)==0:
        print(model)
        continue
    normalized_execution_time = total_execution_time/total_canonical_solution_execution_time
    normalized_max_memory_usage = total_max_memory_usage/total_canonical_solution_max_memory_usage
    normalized_memory_usage = total_memory_usage / total_canonical_solution_memory_usage
    total_execution_time = total_execution_time/len(normalized_execution_time_list)
    total_memory_usage = total_memory_usage/len(normalized_execution_time_list)
    total_max_memory_usage = total_max_memory_usage/len(normalized_execution_time_list)


    pass1 = len(normalized_execution_time_list)/1000*100

    print(f"{model}&{total_execution_time:.2f}&{normalized_execution_time:.2f}&{total_max_memory_usage:.2f}&{normalized_max_memory_usage:.2f}&{total_memory_usage:.2f}&{normalized_memory_usage:.2f}\\\\")
    save_results.append(
        {
            "model":model,
            "ET":float(f"{total_execution_time:.2f}"),
            "NET":float(f"{normalized_execution_time:.2f}"),
            "MU":float(f"{total_max_memory_usage:.2f}"),
            "NMU":float(f"{normalized_max_memory_usage:.2f}"),
            "TMU":float(f"{total_memory_usage:.2f}"),
            "NTMU":float(f"{normalized_memory_usage:.2f}"),
        }
    )

import csv

# Define the CSV file path
csv_file_path = "./humaneval_efficiency_report.csv"

# Write to CSV file
with open(csv_file_path, mode='w', newline='') as file:
    # Define the fieldnames (column names) based on the keys of the dictionary
    fieldnames = ["model", "ET", "NET", "MU", "NMU", "TMU", "NTMU"]

    # Create a DictWriter object
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    # Write the header (column names)
    writer.writeheader()

    # Write the rows
    for result in save_results:
        writer.writerow(result)

print(f"Results have been saved to {csv_file_path}")
