from luna.metrics_appeval_collection import MetricsAppEvalCollections
import luna.data_loader as data_loader

from types import SimpleNamespace
import matplotlib.pyplot as plt
import seaborn as sns
from copy import deepcopy
import numpy as np
from scipy.stats import mannwhitneyu, rankdata
import os
import json
import argparse


def compute_A12(sample1, sample2):
    # Combine the samples
    combined = np.concatenate([sample1, sample2])

    # Rank the combined sample
    ranks = rankdata(combined)

    # Get the ranks for sample1
    ranks_sample1 = ranks[: len(sample1)]

    # Calculate R1, the sum of ranks for sample1
    R1 = np.sum(ranks_sample1)

    # Calculate A12
    m = len(sample1)
    n = len(sample2)
    A12 = (R1 / m - (m + 1) / 2) / n

    return A12


def rq1(state_abstract_args, prob_args, train_instances, val_instances, test_instances):
    state_abstract_args_obj = SimpleNamespace(**state_abstract_args)
    prob_args_obj = SimpleNamespace(**prob_args)

    metrics_obj = MetricsAppEvalCollections(
        state_abstract_args_obj,
        prob_args_obj,
        train_instances,
        val_instances,
        test_instances,
    )

    # Dictionary to store results
    results = {}
    results[
        "transition_KL_divergence_instance_level"
    ] = metrics_obj.transition_KL_divergence_instance_level()

    results["transition_matrix_list"] = metrics_obj.transition_matrix_list()

    results[
        "stationary_distribution_entropy"
    ] = metrics_obj.stationary_distribution_entropy()

    return results


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

    eval_folder_path = "eval/{}/{}".format(dataset, extract_block_idx_str)
    if not os.path.exists(eval_folder_path):
        os.makedirs(eval_folder_path)

    loader = None
    if dataset == "truthful_qa" or dataset == "truthful_qa_alpaca":
        loader = data_loader.TqaDataLoader(dataset_folder_path, llm_name)

    elif dataset == "advglue++" or dataset == "advglue++_alpaca":
        loader = data_loader.AdvDataLoader(
            dataset_folder_path, llm_name, is_attack_success
        )

    elif dataset == "sst2" or dataset == "sst2_alpaca":
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

    # elif info_type == "attention_heads" or info_type == "attention_blocks":
    #     if info_type == "attention_heads":
    #         print("Loading attention heads...")
    #         (
    #             train_instances,
    #             val_instances,
    #             test_instances,
    #         ) = loader.load_attentions(0)
    #         print("Finished loading attention heads!")
    #     else:
    #         print("Loading attention blocks...")
    #         (
    #             train_instances,
    #             val_instances,
    #             test_instances,
    #         ) = loader.load_attentions(1)
    #         print("Finished loading attention blocks!")
    else:
        raise NotImplementedError("Unknown info type!")
    return train_instances, val_instances, test_instances


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--result_save_path",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    model_datasets_dict = {
        "advglue++_alpaca": "alpaca_7B",
        "sst2_alpaca": "alpaca_7B",
        "truthful_qa_alpaca": "alpaca_7B_with_semantics",
        "advglue++": "llama2_7B",
        "sst2": "llama2_7B",
        "truthful_qa": "llama2_7B_with_semantics",
        "humaneval": "codellama-13b-Instruct",
        "mbpp": "codellama-13b-Instruct",
        "tl_code_sum": "codellama-13b-Instruct_with_semantic",
        "code_search_net_java": "codellama-13b-Instruct_with_semantic",
    }

    datasets = {
        "advglue++_alpaca": "Grid_10_3_DTMC_0_1",
        "sst2_alpaca": "Grid_5_3_DTMC_0_1",
        "truthful_qa_alpaca": "GMM_400_2048_DTMC_0_0",
        "advglue++": "Grid_10_3_DTMC_0_1",
        "sst2": "Grid_5_3_DTMC_0_1",
        "truthful_qa": "GMM_400_2048_DTMC_0_0",
        "humaneval": "GMM_200_1024_DTMC_0_0",
        "mbpp": "GMM_200_1024_DTMC_0_0",
        "code_search_net_java": "GMM_200_1024_DTMC_0_0",
        "tl_code_sum": "KMeans_400_1024_DTMC_0_0",
    }

    info_type = "hidden_states"
    fig_kde, axs_kde = plt.subplots(
        2, 5, figsize=(20, 7)
    ) 

    idx = 0
    result = {}
    for dataset_key, optimal_setting in datasets.items():
        axs_kde_flat = axs_kde.reshape(-1)
        
        settings = optimal_setting.split("_")
        # remove _alpaca in string
        dataset = dataset_key.replace("_alpaca", "")
    
        state_abstract_args = {
            "llm_name": model_datasets_dict[dataset_key],
            "result_save_path": args.result_save_path,
            "dataset": dataset,
            "cluster_method": settings[0],
            "abstract_state": int(settings[1]),
            "test_ratio": 0.2,
            "extract_block_idx": "31",
            "info_type": info_type,
            "pca_dim": int(settings[2]),
            "is_attack_success": 1,
            "grid_history_dependency_num": int(settings[5]),
            "result_eval_path": "{}/eval/{}".format(args.result_save_path, model_datasets_dict[dataset_key]),
        }

        prob_args = {
            "dataset": dataset,
            "cluster_method": settings[0],
            "abstract_state": int(settings[1]),
            "test_ratio": 0.2,
            "extract_block_idx": "31",
            "info_type": info_type,
            "pca_dim": int(settings[2]),
            "is_attack_success": 1,
            "hmm_components_num": int(settings[4]),
            "iter_num": 2,
            "model_type": settings[3],
            "grid_history_dependency_num": int(settings[5]),
        }

        train_instances_loaded, val_instances_loaded, test_instances_loaded = load_data(
            state_abstract_args
        )

        train_instances = deepcopy(train_instances_loaded)
        val_instances = deepcopy(val_instances_loaded)
        test_instances = deepcopy(test_instances_loaded)

        results = rq1(
            state_abstract_args,
            prob_args,
            train_instances,
            val_instances,
            test_instances,
        )
        train_probs, val_probs, test_probs = results["transition_matrix_list"]

        print(max(train_probs), max(test_probs), max(val_probs))
        print(min(train_probs), min(test_probs), min(val_probs))

        # Update the KDE plots
        num_samples = 10000
        train_probs = np.array(train_probs)
        test_probs = np.array(test_probs)
        val_probs = np.array(val_probs)
        # For test_probs
        sampled_indices_test = np.random.choice(
            np.arange(len(test_probs)), size=num_samples, p=test_probs / sum(test_probs)
        )

        sns.kdeplot(
            sampled_indices_test,
            fill=True,
            color="darkred",
            label="TestAbnormal",
            linewidth=2,
            ax=axs_kde_flat[idx],
        )

        sampled_indices_val = np.random.choice(
            np.arange(len(val_probs)), size=num_samples, p=val_probs / sum(val_probs)
        )
        sns.kdeplot(
            sampled_indices_val,
            fill=True,
            color="darkblue",
            label="TestNormal",
            linewidth=2,
            ax=axs_kde_flat[idx],
        )

        sampled_indices_train = np.random.choice(
            np.arange(len(train_probs)),
            size=num_samples,
            p=train_probs / sum(train_probs),
        )
        sns.kdeplot(
            sampled_indices_train,
            fill=True,
            color="darkgreen",
            label="TrainNormal",
            linewidth=2,
            ax=axs_kde_flat[idx],
        )
        dataset_perspective_dict = {
            "truthful_qa_alpaca": "TruthfulQA - A",
            "sst2_alpaca": "SST-2 - A",
            "advglue++_alpaca": "AdvGLUE++ - A",
            "truthful_qa": "TruthfulQA - L",
            "sst2": "SST-2 - L",
            "advglue++": "AdvGLUE++ - L",
            "humaneval": "HumanEval - C",
            "mbpp": "MBPP - C",
            "code_search_net_java": "CodeSearchNet-Java - C",
            "tl_code_sum": "TL-CodeSum - C"
        }
        axs_kde_flat[idx].set_title(f"{dataset_perspective_dict[dataset_key]}", fontsize=16)
        axs_kde_flat[idx].set_xticks([])
        axs_kde_flat[idx].set_xlim([0, None])
        if idx == 0 or idx == 5:
            if idx == 0:
                axs_kde_flat[idx].legend(loc="upper left", fontsize="x-small")
            axs_kde_flat[idx].set_ylabel("Density", fontsize="14")
        else:
            axs_kde_flat[idx].set_ylabel("")
            axs_kde_flat[idx].legend().remove()
        
        idx += 1

        # Update the KL Divergence plots
        # transition_distribution_divergence = np.array(
        #     transition_distribution_divergence
        # )
        # transition_distribution_divergence = transition_distribution_divergence[
        #     np.isfinite(transition_distribution_divergence)
        # ]
        # sns.kdeplot(transition_distribution_divergence, fill=True, ax=axs_kl[idx])

        # axs_kl[idx].set_title(f"KL Divergence for {dataset}", fontsize=16)
        # axs_kl[idx].set_xlabel("KL Divergence", fontsize=14)
        # axs_kl[idx].set_ylabel("Density", fontsize=14)
        # # axs_kl[idx].grid(True, linestyle='--', linewidth=0.5, color='gray')
        

        # Mann-Whitney U-test
        u_statistic, p_value = mannwhitneyu(
            val_probs, test_probs, alternative="two-sided"
        )
        print(f"{dataset} U-statistic: {u_statistic}")
        print(f"{dataset} P-value: {p_value}")

        # Compute A12 effect size
        A12 = compute_A12(test_probs, val_probs)
        print(f"{dataset} A12: {A12}")

        result[dataset_key] = {
            "kde": {
                "train_probs": train_probs.tolist(),
                "test_probs": test_probs.tolist(),
                "val_probs": val_probs.tolist(),
            },
            # "kl_divergence": transition_distribution_divergence.tolist(),
            "mannwhitneyu": {
                "u_statistic": u_statistic,
                "p_value": p_value,
            },
        }
    # Save plots
    fig_kde.tight_layout()
    fig_kde.savefig("eval/plot/RQ1_KDE_comparison.pdf",  format='pdf', dpi=1200, bbox_inches='tight')
    # fig_kl.tight_layout()
    # fig_kl.savefig("eval/RQ1_KL_Divergence_comparison.pdf")
    # save the results to json
    with open("eval/plot/RQ1.json", "w") as f:
        json.dump(result, f)


if __name__ == "__main__":
    main()
