import os
import json
from datasets import load_dataset
import random

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return

def writer(data, save_dir, file_type):
    
    save_path = "/".join([save_dir, file_type + ".json"])
    
    with open(save_path, "w") as f:
        json.dump(data, f, indent=4)

def transform_data_and_save_in_file(data, save_dir, file_type):
    data_list = []
    for sample in data:
        data_list.append({
            "instruction": sample["system_prompt"],
            "input": sample["user_prompt"],
            "output": sample["answer"],
            "answer": sample["answer"],
        })
    random.shuffle(data_list)
    try:
        writer(data_list, save_dir, file_type)
        return True
    except Exception as e:
        print(e)
        print("Error in writing file")
        return False

finance_ds = load_dataset("sujet-ai/Sujet-Finance-Instruct-177k",split="train")
finance_ds = finance_ds.train_test_split(train_size=0.6, seed=42)

finance_ds_train = finance_ds["train"]

finance_ds_test_val = finance_ds["test"]
finance_ds_test_val = finance_ds_test_val.train_test_split(train_size=0.5,seed=42)

finance_ds_test = finance_ds_test_val["train"]
finance_ds_val = finance_ds_test_val["test"]

save_dir = "dataset/subject-finance-instruct-177k"

create_dir(save_dir)

transform_train = transform_data_and_save_in_file(finance_ds_train, save_dir, "train")
transform_test = transform_data_and_save_in_file(finance_ds_test, save_dir, "test")
transform_val = transform_data_and_save_in_file(finance_ds_val, save_dir, "val")

print("==============finish======================")
print("transform_train: {}, transform_test: {}, transform_val: {}".format(transform_train, transform_test, transform_val))
print("==========================================")


