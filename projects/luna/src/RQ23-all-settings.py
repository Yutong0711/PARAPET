from luna.metrics_appeval_collection import MetricsAppEvalCollections
import luna.data_loader as data_loader

from types import SimpleNamespace
import pandas as pd
from itertools import product
from collections import defaultdict
import os
from copy import deepcopy
import numpy as np
from scipy.stats import mannwhitneyu
import argparse


def write_result_to_csv(
    result, settings_str, eval_foloder_path
):
    path = "{}/rq23_all_settings.csv".format(
        eval_foloder_path
    )
    result["settings"] = settings_str  # Add settings to the result

    dict_result = {
        "abstract_model_perplexity_good": result["perplexity_abstract_model"][0],
        "abstract_model_perplexity_bad": result["perplexity_abstract_model"][1],
        "abstract_model_smoothed_perplexity_2_good": result[
            "smoothed_perplexity_abstract_model"
        ][2][0],
        "abstract_model_smoothed_perplexity_2_bad": result[
            "smoothed_perplexity_abstract_model"
        ][2][1],
        "abstract_model_smoothed_perplexity_3_good": result[
            "smoothed_perplexity_abstract_model"
        ][3][0],
        "abstract_model_smoothed_perplexity_3_bad": result[
            "smoothed_perplexity_abstract_model"
        ][3][1],
        "abstract_model_smoothed_perplexity_4_good": result[
            "smoothed_perplexity_abstract_model"
        ][4][0],
        "abstract_model_smoothed_perplexity_4_bad": result[
            "smoothed_perplexity_abstract_model"
        ][4][1],
        "settings": result["settings"],
    }
    for key, value in dict_result.items():
        result[key] = value
    del result["smoothed_perplexity_abstract_model"]
    del result["perplexity_abstract_model"]

    for key, value in result["stationary_distribution_entropy_dict"].items():
        result[key] = value
    del result["stationary_distribution_entropy_dict"]

    df = pd.DataFrame([result])  # Create a DataFrame for the single result
    if not os.path.isfile(path):
        print("Creating new file")
        df.to_csv(
            path, mode="w", index=False, header=True
        )  # Write with header if file doesn't exist
    else:
        print("Appending to existing file")
        df.to_csv(
            path, mode="a", index=False, header=False
        )  # Append without header if file exists


def rq3(state_abstract_args, prob_args, train_instances, val_instances, test_instances):
    state_abstract_args_obj = SimpleNamespace(**state_abstract_args)
    prob_args_obj = SimpleNamespace(**prob_args)

    try:
        eval_obj = MetricsAppEvalCollections(
            state_abstract_args_obj,
            prob_args_obj,
            train_instances,
            val_instances,
            test_instances,
        )
    except Exception as e:
        print(e)
        return None

    (
        aucroc,
        _,
        _,
    ) = eval_obj.get_eval_result()
    eval_result_dict = {
        "aucroc": aucroc,
    }

    preciseness = eval_obj.preciseness()
    entropy = eval_obj.entropy()
    probabilistic_reasoning = eval_obj.probabilistic_reasoning()
    value_diversity_instant_level = eval_obj.value_diversity_instant_level()
    value_diversity_n_gram_level = eval_obj.value_diversity_n_gram_level()
    derivative_diversity_n_gram_level = eval_obj.derivative_diversity_n_gram_level()
    second_derivative_diversity_n_gram_level = (
        eval_obj.second_derivative_diversity_n_gram_level()
    )

    eval_result_dict["transition_matrix_list"] = eval_obj.transition_matrix_list()

    eval_result_dict["preciseness_mean"] = preciseness[0]
    eval_result_dict["preciseness_max"] = preciseness[1]

    eval_result_dict["entropy_val"] = entropy[0]
    eval_result_dict["entropy_test"] = entropy[1]

    eval_result_dict["probabilistic_reasoning_divergence"] = probabilistic_reasoning

    eval_result_dict[
        "value_diversity_instant_level_val"
    ] = value_diversity_instant_level[0]
    eval_result_dict[
        "value_diversity_instant_level_test"
    ] = value_diversity_instant_level[1]

    eval_result_dict["value_diversity_n_gram_level_val"] = value_diversity_n_gram_level[
        0
    ]
    eval_result_dict[
        "value_diversity_n_gram_level_test"
    ] = value_diversity_n_gram_level[1]

    eval_result_dict[
        "derivative_diversity_n_gram_level_val_increasing"
    ] = derivative_diversity_n_gram_level[0]
    eval_result_dict[
        "derivative_diversity_n_gram_level_val_decreasing"
    ] = derivative_diversity_n_gram_level[1]
    eval_result_dict[
        "derivative_diversity_n_gram_level_test_increasing"
    ] = derivative_diversity_n_gram_level[2]
    eval_result_dict[
        "derivative_diversity_n_gram_level_test_decreasing"
    ] = derivative_diversity_n_gram_level[3]

    eval_result_dict[
        "second_derivative_diversity_n_gram_level_val_increasing"
    ] = second_derivative_diversity_n_gram_level[0]
    eval_result_dict[
        "second_derivative_diversity_n_gram_level_val_decreasing"
    ] = second_derivative_diversity_n_gram_level[1]
    eval_result_dict[
        "second_derivative_diversity_n_gram_level_test_increasing"
    ] = second_derivative_diversity_n_gram_level[2]
    eval_result_dict[
        "second_derivative_diversity_n_gram_level_test_decreasing"
    ] = second_derivative_diversity_n_gram_level[3]

    eval_result_dict["succinctness"] = eval_obj.succinctness()
    eval_result_dict["coverage"] = eval_obj.state_coverage()
    eval_result_dict["sensitivity"] = eval_obj.sensitivity()
    eval_result_dict["sink_state"] = eval_obj.sink_state()
    eval_result_dict["source_state"] = eval_obj.source_state()
    eval_result_dict["recurrent_state"] = eval_obj.recurrent_state()
    eval_result_dict[
        "stationary_distribution_entropy_dict"
    ] = eval_obj.stationary_distribution_entropy()
    eval_result_dict["perplexity_abstract_model"] = eval_obj.perplexity_abstract_model()
    eval_result_dict[
        "smoothed_perplexity_abstract_model"
    ] = eval_obj.smoothed_perplexity_abstract_model()

    return eval_result_dict

def run_experiment(
    args,
    train_instances,
    val_instances,
    test_instances,
    abstraction_method,
    abstract_state_num,
    pca_dim,
    model_type,
    hmm_n_comp=None,
    grid_history_dependency_num=None,
):
    state_abstract_args = {
        "llm_name": args["llm_name"],
        "result_save_path": args["result_save_path"],
        "dataset": args["dataset"],
        "test_ratio": 0.2,
        "extract_block_idx": args["extract_block_idx"],
        "info_type": args["info_type"],
        "is_attack_success": 1,
        "cluster_method": abstraction_method,
        "abstract_state": abstract_state_num,
        "pca_dim": pca_dim,
        "grid_history_dependency_num": grid_history_dependency_num
        if grid_history_dependency_num
        else "",
    }

    prob_args = {
        "dataset": args["dataset"],
        "test_ratio": 0.2,
        "extract_block_idx": args["extract_block_idx"],
        "info_type": args["info_type"],
        "is_attack_success": 1,
        "iter_num": 10,
        "cluster_method": abstraction_method,
        "abstract_state": abstract_state_num,
        "pca_dim": pca_dim,
        "model_type": model_type,
        "hmm_components_num": hmm_n_comp if hmm_n_comp else "",
        "grid_history_dependency_num": grid_history_dependency_num
        if grid_history_dependency_num
        else "",
    }

    settings_str = "{}_{}_{}_{}_{}_{}".format(
        abstraction_method,
        abstract_state_num,
        pca_dim,
        model_type,
        hmm_n_comp if hmm_n_comp else "0",
        grid_history_dependency_num if grid_history_dependency_num else "0",
    )

    # Call the rq3 function and return the result
    result = rq3(
        state_abstract_args, prob_args, train_instances, val_instances, test_instances
    )
    # Handle the case when the experiment fails
    if result is None:
        return None, None
    
    train_probs, test_probs, val_probs = result["transition_matrix_list"]
    test_probs = np.array(test_probs)
    val_probs = np.array(val_probs)
    _, p_value = mannwhitneyu(test_probs, val_probs, alternative="two-sided")
    # if p_value < 0.05:
    #     return result, settings_str
    # else:
    #     return None, None
    return result, settings_str


def load_data(state_abstract_args):
    args = SimpleNamespace(**state_abstract_args)
    llm_name = args.llm_name
    result_save_path = args.result_save_path
    dataset = args.dataset
    info_type = args.info_type
    extract_block_idx_str = args.extract_block_idx
    is_attack_success = args.is_attack_success

    dataset_folder_path = "{}/{}/{}".format(
        result_save_path, dataset, extract_block_idx_str
    )
    if not os.path.exists(dataset_folder_path):
        os.makedirs(dataset_folder_path)

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
    else:
        raise NotImplementedError("Unknown info type!")
    return train_instances, val_instances, test_instances


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result_save_path",
        type=str,
        required=True
    )
    parser.add_argument("--llm", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)

    args = parser.parse_args()

    # Experiment settings
    llm = args.llm
    dataset = args.dataset
    info_type = "hidden_states"
    extract_block_idx = "31"
    abstraction_methods = ["Grid-based", "Cluster-based"]
    partition_nums = [5, 10, 15]
    abstraction_states = [200, 400, 600]
    cluster_methods = ["GMM", "KMeans"]
    pca_dims = [512, 1024, 2048]
    grid_pca_dims = [3, 5]
    probability_models = ["DTMC", "HMM"]
    hmm_n_comps = [100, 200, 400]
    grid_history_dependency = [1, 2, 3]
    grid_hmm_n_comps = [100, 200, 400]
    state_abstract_args = {
        "llm_name": llm,
        "result_save_path": args.result_save_path,
        "dataset": dataset,
        "test_ratio": 0.2,
        "extract_block_idx": extract_block_idx,
        "info_type": info_type,
        "is_attack_success": 1,
    }

    train_instances_loaded, val_instances_loaded, test_instances_loaded = load_data(
        state_abstract_args
    )

    eval_folder_path = "eval/{}/{}/{}/{}".format(dataset, llm, info_type, extract_block_idx)
    if not os.path.exists(eval_folder_path):
        os.makedirs(eval_folder_path)
    # Iterate through each abstraction method (Grid-based and Cluster-based)
    for abstraction_method in abstraction_methods:
        # If Grid-based abstraction method is chosen
        if abstraction_method == "Grid-based":
            # Iterate through possible partition numbers for the grid-based method
            for partition_num in partition_nums:
                # Explore the impact of different PCA dimensions
                for pca_dim in grid_pca_dims:
                    # Explore results for different probability models (DTMC and HMM)
                    for model_type in probability_models:
                        # Explore different numbers of Grid history dependency
                        for grid_history_dependency_num in grid_history_dependency:
                            # If the model is Hidden Markov Model (HMM)
                            if model_type == "HMM":
                                # Iterate over different numbers of HMM components
                                for hmm_n_comp in grid_hmm_n_comps:
                                    train_instances = deepcopy(train_instances_loaded)
                                    val_instances = deepcopy(val_instances_loaded)
                                    test_instances = deepcopy(test_instances_loaded)
                                    result, settings_str = run_experiment(
                                        state_abstract_args,
                                        train_instances,
                                        val_instances,
                                        test_instances,
                                        "Grid",
                                        partition_num,
                                        pca_dim,
                                        model_type,
                                        hmm_n_comp=hmm_n_comp,
                                        grid_history_dependency_num=grid_history_dependency_num,
                                    )
                                    if result:
                                        write_result_to_csv(
                                            result,
                                            settings_str,
                                            eval_folder_path
                                        )

                            else:
                                train_instances = deepcopy(train_instances_loaded)
                                val_instances = deepcopy(val_instances_loaded)
                                test_instances = deepcopy(test_instances_loaded)
                                result, settings_str = run_experiment(
                                    state_abstract_args,
                                    train_instances,
                                    val_instances,
                                    test_instances,
                                    "Grid",
                                    partition_num,
                                    pca_dim,
                                    model_type,
                                    grid_history_dependency_num=grid_history_dependency_num,
                                )
                                if result:
                                    write_result_to_csv(
                                        result,
                                        settings_str,
                                        eval_folder_path
                                    )

        # If Cluster-based abstraction method is chosen
        elif abstraction_method == "Cluster-based":
            # (similar logic as above for cluster-based experiments)
            for abstraction_state, cluster_method in product(
                abstraction_states, cluster_methods
            ):
                for pca_dim in pca_dims:
                    for model_type in probability_models:
                        if model_type == "HMM":
                            for hmm_n_comp in hmm_n_comps:
                                train_instances = deepcopy(train_instances_loaded)
                                val_instances = deepcopy(val_instances_loaded)
                                test_instances = deepcopy(test_instances_loaded)
                                result, settings_str = run_experiment(
                                    state_abstract_args,
                                    train_instances,
                                    val_instances,
                                    test_instances,
                                    cluster_method,
                                    abstraction_state,
                                    pca_dim,
                                    model_type,
                                    hmm_n_comp=hmm_n_comp,
                                )
                                if result:
                                    write_result_to_csv(result, settings_str, eval_folder_path)
                        else:
                            train_instances = deepcopy(train_instances_loaded)
                            val_instances = deepcopy(val_instances_loaded)
                            test_instances = deepcopy(test_instances_loaded)
                            result, settings_str = run_experiment(
                                state_abstract_args,
                                train_instances,
                                val_instances,
                                test_instances,
                                cluster_method,
                                abstraction_state,
                                pca_dim,
                                model_type,
                            )
                            if result:
                                write_result_to_csv(result, settings_str, eval_folder_path)


if __name__ == "__main__":
    main()
