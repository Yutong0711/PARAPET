import os
import json
from datasets import load_dataset
import random
import pandas as pd
import json 

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    return

def writer(data, save_dir, file_type):
    
    save_path = "/".join([save_dir, file_type + ".json"])
    
    with open(save_path, "w") as f:
        json.dump(data, f, indent=4)



def transform_data_to_save_in_file(file_path, save_dir, file_type):
    with open(file_path) as fp:
        data = json.load(fp)

    data_list = []
    for one_sample in data:
        one_datapoint = {}
        one_datapoint["instruction"] = "What is the stance of the corporate climate policy engagement for \"" + one_sample["query"]+"\" with the given statement? Answer in one of the following 5 options: no_position_or_mixed_position, not_supporting, opposing, strongly_supporting, supporting. \n"
        one_datapoint["input"] = "Statement: "+one_sample["input"]
        one_datapoint["output"] = "Stance: "+one_sample["stance"]
        one_datapoint["answer"] = one_sample["stance"]

        data_list.append(one_datapoint)
    random.shuffle(data_list)
    try:
        writer(data_list, save_dir, file_type)
        return True
    except Exception as e:
        print(e)
        print("Error in writing file")
        return False


save_dir = "dataset/climate_change_claims"
create_dir(save_dir)

train_file_path = "ft-training_set/climate_change_dataset/train.comment.json"
test_file_path = "ft-training_set/climate_change_dataset/test.comment.json"
val_file_path = "ft-training_set/climate_change_dataset/valid.comment.json"

"""possible stance: {'no_position_or_mixed_position',
 'not_supporting',
 'opposing',
 'strongly_supporting',
 'supporting'}"""
 
transform_train = transform_data_to_save_in_file(train_file_path, save_dir, "train")
transform_test = transform_data_to_save_in_file(test_file_path, save_dir, "test")
transform_val = transform_data_to_save_in_file(val_file_path, save_dir, "val")

print("==============finish======================")
print("transform_train: {}, transform_test: {}, transform_val: {}".format(transform_train, transform_test, transform_val))
print("==========================================")