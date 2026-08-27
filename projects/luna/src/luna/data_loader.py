import os
from joblib import load
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from luna.utils.natural_language_metrics import Rouge as Rouge

class DataLoader:
    def __init__(self, dataset_path, llm_name):
        self.dataset_path = dataset_path
        self.llm_name = llm_name

    @staticmethod
    def add_key(dict_obj, key, value):
        dict_obj[key] = value
        return dict_obj


class TqaDataLoader(DataLoader):
    threshold = 0.5

    def load_data(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]
        return file_list[0]
    
    def classify_loop(self, qa_string):
        first_a_index = qa_string.find("A: ")
        is_loop_generated = 0
        if first_a_index != -1:
            answer = qa_string[first_a_index:].strip()
            q_count = answer.count("Q:")
            is_loop_generated = 1 if q_count > 1 else 0
            
        return is_loop_generated

    def load_hidden_states(self):
        all_instances = []
        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("Loading hidden states...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading hidden states")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)
                    # ========= 1. Get the binary label =========
                    binary_label = 1 if data["truth_prob"] > self.threshold else 0
                    # ========= 2. Get the hidden states =========
                    hidden_states = data["hidden_states"]
                    instance_hidden_states = {
                        "id": id,
                        "truth_prob": data["truth_prob"],
                        "hidden_states": hidden_states,
                        "binary_label": binary_label,
                        "is_loop_generated": self.classify_loop(data["A"]),
                        "question": data["Q"],
                        "original_data_record": data["original_data_record"],
                        "answer": data["A"],
                        "probs": data["probs"] if "probs" in data else None,
                        "loss": data["loss"] if "loss" in data else None,
                    }
                    id += 1

                    all_instances.append(instance_hidden_states)
                except EOFError:
                    break

        train_instances, test_instances = train_test_split(
            all_instances, test_size=0.2, random_state=42
        )

        train_instances, val_instances = train_test_split(
            train_instances, test_size=0.2, random_state=42
        )

        return train_instances, val_instances, test_instances

    def load_attentions(self, head_or_block):  # 0 is head, 1 is block
        all_train_instances = []
        test_instances = []

        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("Loading attentions...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading attention")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)
                    # ========= 1. Get the binary label =========
                    binary_label = 1 if data["truth_prob"] > self.threshold else 0
                    # ========= 2. Get the attention =========
                    data["binary_label"] = binary_label
                    data["hidden_states"] = None
                    instance = {
                        "id": id,
                        "attention": data["step_by_step_attention_heads"]
                        if head_or_block == 0
                        else data["step_by_step_attention_blocks"],
                        "binary_label": binary_label,
                        "original_data_record": data["original_data_record"],
                        "probs": data["probs"] if "probs" in data else None,
                        "loss": data["loss"] if "loss" in data else None,
                    }
                    id += 1
                    if data["binary_label"] == 0:
                        test_instances.append(instance)
                    else:
                        all_train_instances.append(instance)
                except EOFError:
                    break

        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        return train_instances, val_instances, test_instances


class AdvDataLoader(DataLoader):
    def __init__(self, dataset_path, llm_name, is_attack_success):
        super().__init__(dataset_path, llm_name)
        self.is_attack_success = is_attack_success

    def classify_sentiment_output(self, output_string):
        lines = output_string.strip().split("\n")
        if len(lines) == 2:
            return 1
        else:
            return 0

    def load_data(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        # Initialize an empty list to store the data
        data_list = []

        # Loop through the file list
        for file in file_list:
            # Load the data from the file
            list_data = load(os.path.join(self.dataset_path, file))
            # Get the file name without the '.joblib' extension
            file_name, _ = os.path.splitext(file)

            # Add the 'ood_method' key to each dictionary in the list
            list_data = [self.add_key(x, "adv_dataset", file_name) for x in list_data]
            # Extend the data_list with the new data
            data_list.extend(list_data)

        return data_list

    def load_hidden_states(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        # Initialize lists to store the data
        all_train_instances = []
        test_instance = []

        # Loop through the file list
        for file in file_list:
            with open("{}/{}".format(self.dataset_path, file), "rb") as f:
                pbar = tqdm(
                    total=None, desc="Loading data from {}".format(file)
                )
                id = 0
                while True:
                    try:
                        pbar.update(1)
                        data = load(f)
                        file_name, _ = os.path.splitext(file)
                        hidden_states = data["hidden_states"]

                        instance_object = {
                            "id": id,
                            "idx": data["original_data_record"]["idx"],
                            "is_attack_success": data["is_attack_success"],
                            "hidden_states": hidden_states,
                            "binary_label": data["label"],
                            "output": data["output"],
                            "input": data["input"],
                            "is_original": 0 if data["is_adversarial"] == 1 else 1,
                            "is_loop_generated": self.classify_sentiment_output(data["output"]),
                            "hidden_states_block_id": data["hidden_states_block_id"],
                            "adv_dataset": file_name.split("_")[-1],
                            "adv_method": data["original_data_record"]["method"]
                            if data["is_adversarial"] == 1
                            else "original",
                            "data_construction": data["original_data_record"][
                                "data_construction"
                            ],
                            "original_data_record": data["original_data_record"],
                            # "probs": data["probs"],
                            # "loss": data["loss"],
                        }
                        id += 1

                        if data["is_adversarial"] == 1:
                            if self.is_attack_success == data["is_attack_success"]:
                                test_instance.append(instance_object)
                        else:
                            all_train_instances.append(instance_object)
                    except EOFError:
                        break
        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        print("Done loading hidden states...")
        return (
            train_instances,
            val_instances,
            test_instance,
        )

    def load_attentions(self, head_or_block):  # 0 is head, 1 is block
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        # Initialize lists to store the data
        all_train_instances = []
        test_instance = []

        # Loop through the file list
        for file in file_list:
            with open("{}/{}".format(self.dataset_path, file), "rb") as f:
                pbar = tqdm(total=None, desc="Loading attentions from {}".format(file))
                id = 0
                while True:
                    try:
                        pbar.update(1)
                        data = load(f)
                        file_name, _ = os.path.splitext(file)
                        instance_object = {
                            "id": id,
                            "idx": data["original_data_record"]["idx"],
                            "is_attack_success": data["is_attack_success"],
                            "attention": data["step_by_step_attention_heads"]
                            if head_or_block == 0
                            else data["step_by_step_attention_blocks"],
                            "binary_label": data["label"],
                            "output": data["output"],
                            "input": data["input"],
                            "is_original": 0 if data["is_adversarial"] == 1 else 1,
                            "attention_block_id": data["hidden_states_block_id"],
                            "adv_dataset": file_name.split("_")[-1],
                            "adv_method": data["original_data_record"]["method"]
                            if data["is_adversarial"] == 1
                            else "original",
                            "data_construction": data["original_data_record"][
                                "data_construction"
                            ],
                            "original_data_record": data["original_data_record"],
                            # "probs": data["probs"],
                            # "loss": data["loss"],
                        }
                        id += 1
                        if data["is_adversarial"] == 1:
                            test_instance.append(instance_object)
                        else:
                            all_train_instances.append(instance_object)
                    except EOFError:
                        break
        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        print("Done loading attentions...")
        return (
            train_instances,
            val_instances,
            test_instance,
        )


class OodDataLoader(DataLoader):
    def classify_sentiment_output(self, output_string):
        lines = output_string.strip().split("\n")
        if len(lines) == 2:
            return 1
        else:
            return 0
        
    def load_hidden_states(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        # Initialize lists to store the data
        all_train_instances = []
        test_instance = []

        # Loop through the file list
        for file in file_list:
            with open("{}/{}".format(self.dataset_path, file), "rb") as f:
                pbar = tqdm(
                    total=None, desc="Loading data from {}".format(file)
                )
                id = 0
                while True:
                    try:
                        pbar.update(1)
                        data = load(f)
                        file_name, _ = os.path.splitext(file)
                        instance_object = {
                            "id": id,
                            "hidden_states": data["hidden_states"],
                            "binary_label": data["label"],
                            "is_id": 0 if data["is_ood"] == 1 else 1,
                            "is_loop_generated": self.classify_sentiment_output(data["output"]),
                            "ood_method": file_name,
                            # "probs": data["probs"],
                            # "loss": data["loss"],
                            "output": data["output"],
                            "input": data["input"],
                        }
                        id += 1
                        if data["is_ood"] == 1:
                            test_instance.append(instance_object)
                        else:
                            all_train_instances.append(instance_object)

                    except EOFError:
                        break

        print("Done loading hidden states...")
        print("Number of train instances: {}".format(len(all_train_instances)))
        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        return (
            train_instances,
            val_instances,
            test_instance,
        )

    def load_attentions(self, head_or_block):  # 0 is head, 1 is block
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        # Initialize an empty list to store the data
        all_train_instances = []
        test_instance = []
        # Loop through the file list
        for file in file_list:
            with open("{}/{}".format(self.dataset_path, file), "rb") as f:
                pbar = tqdm(total=None, desc="Loading attentions from {}".format(file))
                id = 0
                while True:
                    try:
                        pbar.update(1)
                        data = load(f)
                        file_name, _ = os.path.splitext(file)

                        instance_object = {
                            "id": id,
                            "attention": data["step_by_step_attention_heads"]
                            if head_or_block == 0
                            else data["step_by_step_attention_blocks"],
                            "binary_label": data["label"],
                            "is_id": 0 if data["is_ood"] == 1 else 1,
                            "ood_method": file_name,
                            "output": data["output"],
                            "input": data["input"],
                            "loss": data["loss"],
                            "probs": data["probs"],
                        }
                        id += 1
                        if data["is_ood"] == 1:
                            test_instance.append(instance_object)
                        else:
                            all_train_instances.append(instance_object)
                    except EOFError:
                        break

        print("Done loading attentions...")
        print("Number of train instances: {}".format(len(all_train_instances)))
        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        return (
            train_instances,
            val_instances,
            test_instance,
        )

class CodeGenLoader(DataLoader):
    def load_data(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        print(self.llm_name, self.dataset_path)
        return file_list[0]

    def load_hidden_states(self):
        all_instances = []
        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("File path: {}".format(file_path))
        print("Loading hidden states...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading hidden states")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)
                    # ========= 1. Get the binary label =========
                    # ========= 2. Get the hidden states =========
                    hidden_states = data["hidden_states"]
                    instance_hidden_states = {
                        "id": id,
                        "hidden_states": hidden_states,
                        "input": data["input"],
                        "original_data_record": data["original_data_record"],
                        "output": data["output"],
                        "binary_label": data["code_output"]["pass@1"],
                        "pass@1": data["code_output"]["pass@1"],
                    }
                    id += 1

                    all_instances.append(instance_hidden_states)

                except EOFError:
                    break

        train_instances, test_instances = train_test_split(
            all_instances, test_size=0.2, random_state=42
        )

        train_instances, val_instances = train_test_split(
            train_instances, test_size=0.2, random_state=42
        )

        return train_instances, val_instances, test_instances

    def load_attentions(self, head_or_block):  # 0 is head, 1 is block
        all_train_instances = []
        test_instances = []

        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("Loading attentions...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading attention")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)
                    # ========= 1. Get the binary label =========
                    # ========= 2. Get the attention =========
                    instance = {
                        "id": id,
                        "input": data["Input"],
                        "output": data["Output"],
                        "attention": data["step_by_step_attention_heads"]
                        if head_or_block == 0
                        else data["step_by_step_attention_blocks"],
                        "original_data_record": data["original_data_record"],
                    }
                    id += 1
                    if data["binary_label"] == 0:
                        test_instances.append(instance)
                    else:
                        all_train_instances.append(instance)
                except EOFError:
                    break

        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        return train_instances, val_instances, test_instances
    
class CodeSummarizationLoader(DataLoader):
    def load_data(self):
        # Get a list of all joblib files in the specified directory
        file_list = [
            f
            for f in os.listdir(self.dataset_path)
            if f.endswith(".joblib") and f.__contains__(self.llm_name)
        ]

        print(self.llm_name, self.dataset_path)
        return file_list[0]
    
    def _post_process_output(self, output):
        search_string = "Generate comment (summarization) for this code"
        start_index = output.find(search_string)
        if start_index != -1:
            # get the substring before the search string
            output = output[:start_index]
        return output.strip()
    
    
    def load_hidden_states(self):
        all_instances = []
        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("File path: {}".format(file_path))
        print("Loading hidden states...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading hidden states")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)

                    # Get Rouge score
                    rouge = Rouge()
                    raw_rouge_score = rouge.evaulate(data["output"], data["ground_truth"])
                    post_process_output = self._post_process_output(data["output"])
                    post_process_rouge_score = rouge.evaulate(post_process_output, data["ground_truth"])
                    instance_hidden_states = {
                        "id": id,
                        "hidden_states": data["hidden_states"],
                        "input": data["input"],
                        "original_data_record": data["original_data_record"],
                        "output": data["output"],
                        "post_process_output": post_process_output,
                        "ground_truth": data["ground_truth"],
                        "raw_rouge_f1": raw_rouge_score,
                        # "binary_label": 1 if raw_rouge_score > 0.3 else 0,
                        "binary_label": data["binary_label"],
                        "post_process_rouge_f1": post_process_rouge_score,
                        "post_process_binary_label": 1 if post_process_rouge_score > 0.5 else 0,
                    }
                    id += 1

                    all_instances.append(instance_hidden_states)

                except EOFError:
                    break

        train_instances, test_instances = train_test_split(
            all_instances, test_size=0.2, random_state=42
        )

        test_instances, val_instances = train_test_split(
            test_instances, test_size=0.5, random_state=42
        )

        return train_instances, val_instances, test_instances

    def load_attentions(self, head_or_block):  # 0 is head, 1 is block
        all_train_instances = []
        test_instances = []

        file_path = "{}/{}".format(self.dataset_path, self.load_data())
        print("Loading attentions...")
        with open(file_path, "rb") as f:
            pbar = tqdm(total=None, desc="Loading attention")
            id = 0
            while True:
                try:
                    pbar.update(1)
                    data = load(f)
                    # ========= 1. Get the binary label =========
                    # ========= 2. Get the attention =========
                    instance = {
                        "id": id,
                        "input": data["Input"],
                        "output": data["Output"],
                        "attention": data["step_by_step_attention_heads"]
                        if head_or_block == 0
                        else data["step_by_step_attention_blocks"],
                        "original_data_record": data["original_data_record"],
                    }
                    id += 1
                    if data["binary_label"] == 0:
                        test_instances.append(instance)
                    else:
                        all_train_instances.append(instance)
                except EOFError:
                    break

        train_instances, val_instances = train_test_split(
            all_train_instances, test_size=0.2, random_state=42
        )

        return train_instances, val_instances, test_instances