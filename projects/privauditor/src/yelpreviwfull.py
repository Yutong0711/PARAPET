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


yelp_ds = load_dataset("yelp_review_full")
save_dir = "dataset/yelp_review_full"

yelp_train = yelp_ds["train"]
yelp_test = yelp_ds["test"]

create_dir(save_dir)

data_list = []
for sample in yelp_train:
    data_list.append({
        "instruction": "I am sharing a review with you. Based on the text in the review, you need to rate the review in one of the following 5 numerical number: 1 or 2 or 3 or 4 or 5. 1 being the lowest and 5 being the highest. \n\n",
        "input": sample["text"],
        "output": "rate: "+str(sample["label"]),
        "answer": sample["label"],
    })
random.shuffle(data_list)
writer(data_list[:-5000], save_dir, "train")    
writer(data_list[-5000:], save_dir, "val")

del data_list

data_list = []
for sample in yelp_test:
    data_list.append({
        "instruction": "I am sharing a review with you. Based on the text in the review, you need to rate the review in one of the following 5 numerical number: 1 or 2 or 3 or 4 or 5. 1 being the lowest and 5 being the highest. \n\n",
        "input": sample["text"],
        "output": "rate: "+str(sample["label"]),
        "answer": sample["label"],
    })
writer(data_list, save_dir, "test")

print("==============finish======================")