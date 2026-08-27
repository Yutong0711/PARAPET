import os
import json
import random


def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return

def writer(data, save_dir, file_type):
    
    save_path = "/".join([save_dir, file_type + ".json"])
    
    with open(save_path, "w") as f:
        json.dump(data, f, indent=4)

full_data_path = "ft-training_set/alpaca_data.json"
save_dir = "dataset/alpaca"


train_set_size = 39000
test_set_size = 10000
val_set_size = 3002

with open(full_data_path, "r") as f:
    ds = json.load(f)

random.shuffle(ds)

train_set = ds[:train_set_size]
test_set = ds[train_set_size:train_set_size+test_set_size]
val_set = ds[train_set_size+test_set_size:]

create_dir(save_dir)

writer(train_set, save_dir, "train")
writer(test_set, save_dir, "test")
writer(val_set, save_dir, "val")

print("==============finish======================")

