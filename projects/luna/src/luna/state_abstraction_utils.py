from luna.abstraction_model import GMM, KMeans, RegularGrid
import luna.data_loader as data_loader
import numpy as np
from tqdm import tqdm
from sklearn.decomposition import PCA
import pickle
import os

class AbstractStateExtraction:
    def __init__(
        self, args, train_instances=None, val_instances=None, test_instances=None
    ):
        """
        Initialize the AbstractStateExtraction class.
        
        Parameters:
            args (object): An object containing various configuration parameters required for state abstraction.
            train_instances (list, optional): A list of training instances. Defaults to None.
            val_instances (list, optional): A list of validation instances. Defaults to None.
            test_instances (list, optional): A list of test instances. Defaults to None.

        Attributes:
            train_instances: A list of training instances.
            val_instances: A list of validation instances.
            test_instances: A list of test instances.
            train_hidden_info: Hidden information associated with training instances.
            val_hidden_info: Hidden information associated with validation instances.
            test_hidden_info: Hidden information associated with test instances.
            pca_model: PCA model for dimensionality reduction.
            pca_train: Transformed training data after PCA.
            pca_val: Transformed validation data after PCA.
            pca_test: Transformed test data after PCA.
            cluster_model: Model for clustering.
            cluster_train: Clustering results for training data.
            cluster_val: Clustering results for validation data.
            cluster_test: Clustering results for test data.
            loss: Loss value (if any).
        """
        #  ============== State abstraction params ==============
        self.args = args
        self.train_instances = None
        self.val_instances = None
        self.test_instances = None
        self.train_hidden_info = None
        self.val_hidden_info = None
        self.test_hidden_info = None
        self.pca_model = None
        self.pca_train = None
        self.pca_val = None
        self.pca_test = None
        self.cluster_model = None
        self.cluster_train = None
        self.cluster_val = None
        self.cluster_test = None
        self.loss = None

        self.main(train_instances, val_instances, test_instances)

    def save_lists(self, list1, list2, list3, filename):
        with open(filename, "wb") as f:
            pickle.dump((list1, list2, list3), f)

    def get_cluster_label_from_pca(
        self,
        partition_model_path,
        cluster_method,
        train_set,
        val_set,
        test_set,
        abstract_state,
        grid_history_dependency_num,
    ):
        """
        Obtain cluster labels for the given data sets using PCA and a specified clustering method.
        
        Parameters:
            cluster_method (str): The clustering method to be used. Options are "GMM", "KMeans", and "Grid".
            train_set (list): The training data set.
            val_set (list): The validation data set.
            test_set (list): The test data set.
            abstract_state (int): The number of abstract states.
            grid_history_dependency_num (int): The number of history dependencies for the grid clustering method.
            
        Attributes:
            cluster_train: Cluster labels for the training data.
            cluster_val: Cluster labels for the validation data.
            cluster_test: Cluster labels for the test data.
            cluster_model: The clustering model used.
            
        Returns:
            tuple: A tuple containing cluster labels for training, validation, and test data respectively.
            
        Raises:
            NotImplementedError: If an unknown clustering method is provided.
        """
        (
            abstraction_model,
            cluster_labels_train,
            cluster_labels_val,
            cluster_labels_test,
        ) = (
            None,
            None,
            None,
            None,
        )
        if cluster_method == "GMM":
            abstraction_model = GMM(abstract_state)
        elif cluster_method == "KMeans":
            abstraction_model = KMeans(abstract_state)
        elif cluster_method == "Grid":
            abstraction_model = RegularGrid(abstract_state, grid_history_dependency_num)
        else:
            raise NotImplementedError("Unknown clustering method!")
        
        (
            cluster_labels_train,
            cluster_labels_val,
            cluster_labels_test,
        ) = abstraction_model.fit_transform(partition_model_path, train_set, val_set, test_set)

        print("Training set size: {}".format(len(cluster_labels_train)))
        print("Validation set size: {}".format(len(cluster_labels_val)))
        print("Test set size: {}".format(len(cluster_labels_test)))
        self.cluster_train = cluster_labels_train
        self.cluster_val = cluster_labels_val
        self.cluster_test = cluster_labels_test

        self.cluster_model = abstraction_model.clustering

        return cluster_labels_train, cluster_labels_val, cluster_labels_test

    def get_trace_from_hidden_states(
        self,
        pca_model_path,
        partition_model_path,
        train_instances,
        val_instances,
        test_instance,
        pca_dim,
        cluster_method,
        abstract_state,
        grid_history_dependency_num,
    ):
        """
        Obtain state traces from hidden states using PCA and a specified clustering method.
        
        This method processes hidden states from instances, applies PCA for dimensionality reduction, 
        then clusters the reduced data to obtain abstract state traces.
        
        Parameters:
            train_instances (list): A list of training instances containing hidden states.
            val_instances (list): A list of validation instances containing hidden states.
            test_instance (list): A list of test instances containing hidden states.
            pca_dim (int): The number of dimensions to reduce to using PCA.
            cluster_method (str): The clustering method to be used. Options are "GMM", "KMeans", and "Grid".
            abstract_state (int): The number of abstract states.
            grid_history_dependency_num (int): The number of history dependencies for the grid clustering method.
            
        Attributes:
            train_hidden_info: Hidden state information for the training data.
            val_hidden_info: Hidden state information for the validation data.
            test_hidden_info: Hidden state information for the test data.
            pca_model: PCA model used for dimensionality reduction.
            cluster_train: Cluster labels for the training data.
            cluster_val: Cluster labels for the validation data.
            cluster_test: Cluster labels for the test data.
            
        Returns:
            tuple: A tuple containing training, validation, and test instances with updated state traces.
            
        Notes:
            - The method updates the hidden states and attention details in the instances with state traces.
            - PCA is applied to reduce the dimensionality of the hidden states.
            - Clustering is performed on the reduced data to obtain state traces.
        """
        # If pca and partition path exists, load them
        print("Get the training, val, and test hidden states np array...")
        train_hidden_states = [i["hidden_states"] for i in train_instances]
        val_hidden_states = (
            [i["hidden_states"] for i in val_instances] if val_instances else []
        )
        test_hidden_states = [i["hidden_states"] for i in test_instance]

        self.train_hidden_info = train_hidden_states
        self.val_hidden_info = val_hidden_states
        self.test_hidden_info = test_hidden_states

        np_train_hidden_states = np.concatenate(train_hidden_states, axis=0)
        np_val_hidden_states = (
            np.concatenate(val_hidden_states, axis=0) if val_hidden_states else None
        )
        np_test_hidden_states = np.concatenate(test_hidden_states, axis=0)

        print("train hidden states shape", np_train_hidden_states.shape)
        if val_instances:
            print("val hidden states shape", np_val_hidden_states.shape)
        print("test hidden states shape", np_test_hidden_states.shape)

        # ========= 3. PCA FIT and Transform =========
        print("PCA dimension: {}, Starting PCA...".format(pca_dim))

        if os.path.exists(pca_model_path):
            print("Loading pca model and partition model...")
            with open(pca_model_path, "rb") as f:
                pca = pickle.load(f)
            
            print("Finished loading pca model!")
        else:
            pca = PCA(n_components=pca_dim)
            pca.fit(np_train_hidden_states)
            # save pca
            with open(pca_model_path, "wb") as f:
                pickle.dump(pca, f)

        self.pca_model = pca

        print("PCA fitting finished!")

        print("PCA transform...")
        if cluster_method == "Grid":
            # for grid, we need to transform each instance to form a list
            pca_train_data = []
            pca_val_data = []
            pca_test_data = []
            for i in range(len(train_hidden_states)):
                pca_train_data.append(pca.transform(train_hidden_states[i]))
            for i in range(len(val_hidden_states)):
                pca_val_data.append(pca.transform(val_hidden_states[i]))
            for i in range(len(test_hidden_states)):
                pca_test_data.append(pca.transform(test_hidden_states[i]))
        else:
            # for other methods, we can transform the whole np array
            pca_train_data = pca.transform(np_train_hidden_states)
            pca_val_data = pca.transform(np_val_hidden_states) if val_instances else []
            pca_test_data = pca.transform(np_test_hidden_states)
        self.pca_train = pca_train_data
        self.pca_val = pca_val_data
        self.pca_test = pca_test_data
        print("PCA transform finished!")

        # ========= 4. Get the input trace =========
        print("Clustering...")
        (
            cluster_labels_train,
            cluster_labels_val,
            cluster_labels_test,
        ) = self.get_cluster_label_from_pca(
            partition_model_path,
            cluster_method,
            pca_train_data,
            pca_val_data,
            pca_test_data,
            abstract_state,
            grid_history_dependency_num,
        )
        print("Clustering finished!")

        # ========= 5. Format the traces based on sentences =========
        print("Format the traces based on sentences...")
        # traverse each instance, give a cluster label to each token
        if cluster_method == "Grid":
            for i, trace in enumerate(cluster_labels_train):
                train_instances[i]["state_trace"] = trace
                train_instances[i]["hidden_states"] = None
                train_instances[i]["step_by_step_attention_heads"] = None
                train_instances[i]["step_by_step_attention_blocks"] = None
            for i, trace in enumerate(cluster_labels_val):
                val_instances[i]["state_trace"] = trace
                val_instances[i]["hidden_states"] = None
                val_instances[i]["step_by_step_attention_heads"] = None
                val_instances[i]["step_by_step_attention_blocks"] = None
            for i, trace in enumerate(cluster_labels_test):
                test_instance[i]["state_trace"] = trace
                test_instance[i]["hidden_states"] = None
                test_instance[i]["step_by_step_attention_heads"] = None
                test_instance[i]["step_by_step_attention_blocks"] = None
        else:
            cluster_label_count = 0
            for instance in tqdm(train_instances, desc="Format train traces"):
                instance_state_trace = []
                for _ in instance["hidden_states"]:
                    state_id = int(cluster_labels_train[cluster_label_count])
                    instance_state_trace.append(state_id)
                    cluster_label_count += 1
                instance["state_trace"] = instance_state_trace
                instance["hidden_states"] = None
                instance["step_by_step_attention_heads"] = None
                instance["step_by_step_attention_blocks"] = None

            if val_instances:
                cluster_label_count = 0
                for instance in tqdm(val_instances, desc="Format val traces"):
                    instance_state_trace = []
                    for _ in instance["hidden_states"]:
                        state_id = int(cluster_labels_val[cluster_label_count])
                        instance_state_trace.append(state_id)
                        cluster_label_count += 1
                    instance["state_trace"] = instance_state_trace
                    instance["hidden_states"] = None
                    instance["step_by_step_attention_heads"] = None
                    instance["step_by_step_attention_blocks"] = None

            cluster_label_count = 0
            for instance in tqdm(test_instance, desc="Format test traces"):
                instance_state_trace = []
                for _ in instance["hidden_states"]:
                    state_id = int(cluster_labels_test[cluster_label_count])
                    instance_state_trace.append(state_id)
                    cluster_label_count += 1
                instance["state_trace"] = instance_state_trace
                instance["hidden_states"] = None
                instance["step_by_step_attention_heads"] = None
                instance["step_by_step_attention_blocks"] = None

        return train_instances, val_instances, test_instance

    def get_trace_from_attention(
        self,
        pca_model_path,
        partition_model_path,
        train_instances,
        val_instances,
        test_instance,
        pca_dim,
        cluster_method,
        abstract_state,
        grid_history_dependency_num,
    ):
       
        print("Get the training, val, and test attention np array...")
        train_attention= [i["attention"] for i in train_instances]
        val_attention = [i["attention"] for i in val_instances]
        test_attention = [i["attention"] for i in test_instance]

        np_train_attention = np.concatenate(train_attention, axis=0)
        np_val_attention = np.concatenate(val_attention, axis=0)
        np_test_attention = np.concatenate(test_attention, axis=0)

        print("train attention shape", np_train_attention.shape)
        print("val attention shape", np_val_attention.shape)
        print("test attention shape", np_test_attention.shape)

        # ========= 3. PCA FIT and Transform =========
        print("PCA dimension: {}, Starting PCA...".format(pca_dim))

        if os.path.exists(pca_model_path):
            print("Loading pca model and partition model...")
            with open(pca_model_path, "rb") as f:
                pca = pickle.load(f)
            
            print("Finished loading pca model!")
        else:
            pca = PCA(n_components=pca_dim)
            pca.fit(np_train_attention)
            # save pca
            with open(pca_model_path, "wb") as f:
                pickle.dump(pca, f)

        self.pca_model = pca

        print("PCA fitting finished!")

        print("PCA transform...")
        if cluster_method == "Grid":
            # for grid, we need to transform each instance to form a list
            pca_train_data = []
            pca_val_data = []
            pca_test_data = []
            for i in range(len(train_attention)):
                pca_train_data.append(pca.transform(train_attention[i]))
            for i in range(len(val_attention)):
                pca_val_data.append(pca.transform(val_attention[i]))
            for i in range(len(test_attention)):
                pca_test_data.append(pca.transform(test_attention[i]))
        else:
            # for other methods, we can transform the whole np array
            pca_train_data = pca.transform(np_train_attention)
            pca_val_data = pca.transform(np_val_attention) if val_instances else []
            pca_test_data = pca.transform(np_test_attention)
        self.pca_train = pca_train_data
        self.pca_val = pca_val_data
        self.pca_test = pca_test_data
        print("PCA transform finished!")

        # ========= 4. Get the input trace =========
        print("Clustering...")
        (
            cluster_labels_train,
            cluster_labels_val,
            cluster_labels_test,
        ) = self.get_cluster_label_from_pca(
            partition_model_path,
            cluster_method,
            pca_train_data,
            pca_val_data,
            pca_test_data,
            abstract_state,
            grid_history_dependency_num,
        )
        print("Clustering finished!")

        # ========= 5. Format the traces based on sentences =========
        print("Format the traces based on sentences...")
        # traverse each instance, give a cluster label to each token
        cluster_label_count = 0
        for instance in tqdm(train_instances, desc="Format train traces"):
            instance_state_trace = []
            for _ in instance["attention"]:
                state_id = int(cluster_labels_train[cluster_label_count])
                instance_state_trace.append(state_id)
                cluster_label_count += 1
            instance["state_trace"] = instance_state_trace
            instance["hidden_states"] = None
            instance["attention"] = None
            instance["step_by_step_attention_heads"] = None
            instance["step_by_step_attention_blocks"] = None

        cluster_label_count = 0
        for instance in tqdm(val_instances, desc="Format val traces"):
            instance_state_trace = []
            for _ in instance["attention"]:
                state_id = int(cluster_labels_val[cluster_label_count])
                instance_state_trace.append(state_id)
                cluster_label_count += 1
            instance["state_trace"] = instance_state_trace
            instance["hidden_states"] = None
            instance["attention"] = None
            instance["step_by_step_attention_heads"] = None
            instance["step_by_step_attention_blocks"] = None

        cluster_label_count = 0
        for instance in tqdm(test_instance, desc="Format test traces"):
            instance_state_trace = []
            for _ in instance["attention"]:
                state_id = int(cluster_labels_test[cluster_label_count])
                instance_state_trace.append(state_id)
                cluster_label_count += 1
            instance["state_trace"] = instance_state_trace
            instance["hidden_states"] = None
            instance["attention"] = None
            instance["step_by_step_attention_heads"] = None
            instance["step_by_step_attention_blocks"] = None

        return train_instances, val_instances, test_instance

    def main(self, train_instances, val_instances, test_instances):
        """
        Main processing method to generate traces for given instances based on configurations.
        
        This method reads configurations from the 'args' attribute, determines the type of information (hidden states or attention)
        to be used for generating traces, applies PCA and clustering, and saves the results.
        
        Parameters:
            train_instances (list): A list of training instances.
            val_instances (list): A list of validation instances.
            test_instances (list): A list of test instances.
            
        Attributes:
            train_instances: Updated training instances with state traces.
            val_instances: Updated validation instances with state traces.
            test_instances: Updated test instances with state traces.
            
        Notes:
            - The method decides the processing steps based on the 'info_type' attribute from 'args'.
            - It uses either hidden states or attention values to generate traces.
            - PCA is applied for dimensionality reduction, followed by clustering.
            - The results are saved to a specified location.
        """
        args = self.args
        llm_name = args.llm_name
        result_save_path = args.result_save_path
        result_eval_path = args.result_eval_path
        dataset = args.dataset
        info_type = args.info_type
        extract_block_idx_str = args.extract_block_idx
        cluster_method = args.cluster_method
        abstract_state = args.abstract_state
        pca_dim = args.pca_dim
        test_ratio = args.test_ratio
        is_attack_success = args.is_attack_success
        grid_history_dependency_num = args.grid_history_dependency_num

        # set the dataset folder path
        dataset_folder_path = "{}/{}/{}".format(
            result_save_path, dataset, extract_block_idx_str
        )
        if not os.path.exists(dataset_folder_path):
            os.makedirs(dataset_folder_path)

        eval_folder_path = "{}/{}/{}".format(
            result_eval_path, dataset, extract_block_idx_str
        )
        if not os.path.exists(eval_folder_path):
            os.makedirs(eval_folder_path)

        pca_model_folder_path = "{}/pca_model/{}".format(dataset_folder_path, llm_name)
        if not os.path.exists(pca_model_folder_path):
            os.makedirs(pca_model_folder_path)

        pca_model_path = "{}/{}_{}_{}_{}_{}_{}_{}.pkl".format(
            pca_model_folder_path,
            info_type,
            cluster_method,
            abstract_state,
            pca_dim,
            test_ratio,
            is_attack_success,
            grid_history_dependency_num,
        )
        
        partition_model_folder_path = "{}/partition_model/{}".format(dataset_folder_path, llm_name)
        if not os.path.exists(partition_model_folder_path):
            os.makedirs(partition_model_folder_path)
        
        partition_model_path = "{}/{}_{}_{}_{}_{}_{}_{}.pkl".format(
            partition_model_folder_path,
            info_type,
            cluster_method,
            abstract_state,
            pca_dim,
            test_ratio,
            is_attack_success,
            grid_history_dependency_num,
        )
        

        if train_instances and val_instances and test_instances:
            if info_type == "hidden_states":
                (
                    train_instances_with_traces,
                    val_instances_with_traces,
                    test_instances_with_traces,
                ) = self.get_trace_from_hidden_states(
                    pca_model_path,
                    partition_model_path,
                    train_instances,
                    val_instances,
                    test_instances,
                    pca_dim,
                    cluster_method,
                    abstract_state,
                    grid_history_dependency_num,
                )
            elif info_type == "attention_heads" or info_type == "attention_blocks":
                (
                    train_instances_with_traces,
                    val_instances_with_traces,
                    test_instances_with_traces,
                ) = self.get_trace_from_attention(
                    train_instances,
                    val_instances,
                    test_instances,
                    pca_dim,
                    cluster_method,
                    abstract_state,
                    grid_history_dependency_num,
                )
            else:
                raise NotImplementedError("Unknown info type!")

        else:
            loader = None
            if dataset == "truthful_qa":
                loader = data_loader.TqaDataLoader(dataset_folder_path, llm_name)

            elif dataset == "advglue++":
                loader = data_loader.AdvDataLoader(
                    dataset_folder_path, llm_name, is_attack_success
                )

            elif dataset == "sst2":
                loader = data_loader.OodDataLoader(dataset_folder_path, llm_name)

            elif dataset == "humaneval" or dataset == "mbpp":
                loader = data_loader.CodeGenLoader(dataset_folder_path, llm_name)

            elif dataset == "code_search_net_java" or dataset == "tl_code_sum":
                loader = data_loader.CodeSummarizationLoader(dataset_folder_path, llm_name)

            else:
                raise NotImplementedError("Unknown dataset!")

            if info_type == "hidden_states":
                print("Loading hidden states...")
                (
                    train_instances,
                    val_instances,
                    test_instances,
                ) = loader.load_hidden_states()
                print("Finished loading hidden states!")

                (
                    train_instances_with_traces,
                    val_instances_with_traces,
                    test_instances_with_traces,
                ) = self.get_trace_from_hidden_states(
                    pca_model_path,
                    partition_model_path,
                    train_instances,
                    val_instances,
                    test_instances,
                    pca_dim,
                    cluster_method,
                    abstract_state,
                    grid_history_dependency_num
                )

            elif info_type == "attention_heads" or info_type == "attention_blocks":
                if info_type == "attention_heads":
                    print("Loading attention heads...")
                    (
                        train_instances,
                        val_instances,
                        test_instances,
                    ) = loader.load_attentions(0)
                    print("Finished loading attention heads!")
                else:
                    print("Loading attention blocks...")
                    (
                        train_instances,
                        val_instances,
                        test_instances,
                    ) = loader.load_attentions(1)
                    print("Finished loading attention blocks!")

                (
                    train_instances_with_traces,
                    val_instances_with_traces,
                    test_instances_with_traces,
                ) = self.get_trace_from_attention(
                    pca_model_path,
                    partition_model_path,
                    train_instances,
                    val_instances,
                    test_instances,
                    pca_dim,
                    cluster_method,
                    abstract_state,
                    grid_history_dependency_num
                )
            else:
                raise NotImplementedError("Unknown info type!")
        
        if dataset == "advglue++":
            if cluster_method == "Grid":
                save_lists_path = "{}/{}_{}_{}_{}_{}_{}_{}.pkl".format(
                    eval_folder_path,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                    grid_history_dependency_num,
                )
            else:
                save_lists_path = "{}/{}_{}_{}_{}_{}_{}.pkl".format(
                    eval_folder_path,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    is_attack_success,
                )
        else:
            if cluster_method == "Grid":
                save_lists_path = "{}/{}_{}_{}_{}_{}_{}.pkl".format(
                    eval_folder_path,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                    grid_history_dependency_num,
                )
            else:
                save_lists_path = "{}/{}_{}_{}_{}_{}.pkl".format(
                    eval_folder_path,
                    info_type,
                    cluster_method,
                    abstract_state,
                    pca_dim,
                    test_ratio,
                )

        self.train_instances = train_instances_with_traces
        self.val_instances = val_instances_with_traces
        self.test_instances = test_instances_with_traces

        self.save_lists(
            train_instances_with_traces,
            val_instances_with_traces,
            test_instances_with_traces,
            save_lists_path,
        )

        print("Finished training and test traces generation!")
