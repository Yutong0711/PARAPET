from luna.state_abstraction_utils import AbstractStateExtraction
from luna.probabilistic_abstraction_model import (
    HmmModel,
    DtmcModel,
)
from types import SimpleNamespace

llm = "alpaca_7B"
dataset = "truthful_qa"
result_save_path = "../../../data/llmAnalysis/songda"
extract_block_idx = 31
info_type = "hidden_states"
abstraction_method = "KMeans"
model_type = "DTMC"
hmm_n_comp = 100
abstract_state_num = 400
pca_dim = 2048
grid_history_dependency_num = 1

state_abstract_args = {
    "llm_name": llm,
    "result_save_path": result_save_path,
    "dataset": dataset,
    "test_ratio": 0.2,
    "extract_block_idx": extract_block_idx,
    "info_type": info_type,
    "is_attack_success": 1,
    "cluster_method": abstraction_method,
    "abstract_state": abstract_state_num,
    "pca_dim": pca_dim,
    "grid_history_dependency_num": grid_history_dependency_num
    if grid_history_dependency_num
    else "",
    "result_eval_path": "{}/eval/{}".format(result_save_path, llm) 
}


prob_args = {
    "llm_name": llm,
    "result_save_path": result_save_path,
    "dataset": dataset,
    "test_ratio": 0.2,
    "extract_block_idx": extract_block_idx,
    "info_type": info_type,
    "is_attack_success": 1,
    "iter_num": 100,
    "cluster_method": abstraction_method,
    "abstract_state": abstract_state_num,
    "pca_dim": pca_dim,
    "model_type": model_type,
    "hmm_components_num": hmm_n_comp if hmm_n_comp else "",
    "grid_history_dependency_num": grid_history_dependency_num
    if grid_history_dependency_num
    else "",
}

stat_dict = {
    'proper_stopped_and_true': 0,
    'proper_stopped_and_false': 0,
    'loop_generated_and_true': 0,
    'loop_generated_and_false': 0
}

abs_args = SimpleNamespace(**state_abstract_args)

# abstractStateExtraction = AbstractStateExtraction(
#     abs_args, None, None, None
# )

dtmc_model = DtmcModel(
    prob_args["dataset"],
    prob_args["extract_block_idx"],
    prob_args["info_type"],
    prob_args["cluster_method"],
    prob_args["abstract_state"],
    prob_args["pca_dim"],
    prob_args["test_ratio"],
    prob_args["is_attack_success"],
    prob_args["grid_history_dependency_num"],
    state_abstract_args["result_eval_path"]
)
(
    dtmc_transition_aucroc,
    dtmc_transition_fpr,
    dtmc_transition_tpr,
) = dtmc_model.get_aucroc_by_transition_binding()

prob_model = dtmc_model
test_abstract_traces = dtmc_model.test_traces
val_abstract_traces = dtmc_model.val_traces
train_abstract_traces = dtmc_model.train_traces

train_data_points = [{} for _ in range(len(train_abstract_traces))]
for i, one_trace in enumerate(train_abstract_traces):
    train_data_points[i]["step_by_step_analyzed_trace"] = one_trace
    train_data_points[i]["label"] = dtmc_model.train_groundtruths[i]

# check train_data_points[i]["label"] ratio


dtmc_model.get_aucroc_by_state_binding()

all_instances = dtmc_model.train_instances + dtmc_model.val_instances + dtmc_model.test_instances
for instance in all_instances:
    classification = instance['is_loop_generated']
    if classification == 0:
        if instance['binary_label'] >= 0.5:
            stat_dict['proper_stopped_and_true'] += 1
        else:
            stat_dict['proper_stopped_and_false'] += 1
    else:
        if instance['binary_label'] >= 0.5:
            stat_dict['loop_generated_and_true'] += 1
        else:
            stat_dict['loop_generated_and_false'] += 1

# calculate stat_dict percentage
total = sum(stat_dict.values())
for key in stat_dict:
    stat_dict[key] /= total



print(stat_dict)