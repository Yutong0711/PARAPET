import argparse
import os
import mteb
from sentence_transformers import SentenceTransformer
from mteb.models import bm25

import time

from models import *
model_class_mappping = {
    'contriever': SentenceTransformer,
    'instructor': InstructorRetriever,
    'sentence': SentenceTransformer,
}


instruction_mappping = {
    "CodeNetBugPreferenceRetrieval": "Please retrieve the correct code.",
    "CodeNetEfficiencyPreferenceRetrieval": "Please retrieve the efficient code.",
    "SaferCodePreferenceRetrieval": "Please retrieve safer code.",
    "DeprecatedCodePreferenceRetrieval": "Please retrieve updated code.",
    "CVEFixesPreferenceRetrieval": "Please retrieve fixed code.",
    "Defects4JPreferenceRetrieval": "Please retrieve correct code.",
    "SQLR2PreferenceRetrieval": "Please retrieve efficient code.",
}

instructor_instruction_mappping = {
    "CodeNetBugPreferenceRetrieval": "Please retrieve the correct code: ",
    "CodeNetEfficiencyPreferenceRetrieval": "Please retrieve efficient code: ",
    "SaferCodePreferenceRetrieval": "Please retrieve safer code: ",
    "DeprecatedCodePreferenceRetrieval": "Please retrieve updated code: ",
    "CVEFixesPreferenceRetrieval": "Please retrieve fixed code: ",
    "Defects4JPreferenceRetrieval": "Please retrieve correct code: ",
    "SQLR2PreferenceRetrieval": "Please retrieve efficient code: ",
}

neg_instruction_mappping = {
    "CodeNetBugPreferenceRetrieval": "Please retrieve the buggy code.",
    "CodeNetEfficiencyPreferenceRetrieval": "Please retrieve the slow code.",
    "SaferCodePreferenceRetrieval": "Please retrieve vulnerable code.",
    "DeprecatedCodePreferenceRetrieval": "Please retrieve outdated code.",
    "CVEFixesPreferenceRetrieval": "Please retrieve the flawed code.",
    "Defects4JPreferenceRetrieval": "Please retrieve the buggy code.",
    "SQLR2PreferenceRetrieval": "Please retrieve slow code.",
}

neg_instructor_instruction_mappping = {
    "CodeNetBugPreferenceRetrieval": "Please retrieve the buggy code: ",
    "CodeNetEfficiencyPreferenceRetrieval": "Please retrieve slow code: ",
    "SaferCodePreferenceRetrieval": "Please retrieve vulnerable code: ",
    "DeprecatedCodePreferenceRetrieval": "Please retrieve outdated code: ",
    "CVEFixesPreferenceRetrieval": "Please retrieve the flawed code: ",
    "Defects4JPreferenceRetrieval": "Please retrieve the buggy code: ",
    "SQLR2PreferenceRetrieval": "Please retrieve slow code: ",
}


def define_model_class(model_name):
    if model_name in model_class_mappping:
        return model_class_mappping[model_name]
    
    for _model_class_name, _model_class in model_class_mappping.items():
        if _model_class_name in model_name:
            return _model_class
    # we set this as the default
    return None

def main(args):
    # for openai
    task_names = args.task_names
    
    print(f"Running evaluation for tasks: {task_names}")

    tasks = mteb.get_tasks(tasks=task_names)
    evaluation = mteb.MTEB(tasks=tasks)
    
    if args.model_class is not None:
        base_model_class = model_class_mappping[args.model_class]  
    else:
        base_model_class = define_model_class(args.model_name)
    
    if base_model_class is not None:
        if args.checkpoint_dir is not None and os.path.exists(args.checkpoint_dir):
            model = base_model_class(args.checkpoint_dir)
        else:
            model = base_model_class(args.model_name)
    elif args.model_name in RepLlaMA_DICT:
        model = RepLlaMA_DICT[args.model_name].load_model()
    elif args.model_name in PROMPTRIEVER_DICT:
        model = PROMPTRIEVER_DICT[args.model_name].load_model()
    else:
        model = mteb.get_model(args.model_name)

    model_str = args.model_name.replace('/', '__')
    # we have to add another directory to save the results of qrels (predictions)
    output_dir = os.path.join(f'./results/{model_str}') if args.output_dir is None else args.output_dir
    
    start_time = time.time()

    if "promptriever" in args.model_name or "instructor" in args.model_name:
        if args.no_instruction is False:
            if "promptriever" in args.model_name:
                if args.neg_instruction is False:
                    instruction = instruction_mappping[args.task_names[0]]
                else:
                    instruction = neg_instruction_mappping[args.task_names[0]]
                    output_dir = os.path.join(f'./results/{model_str}_neg_instruction') if args.output_dir is None else args.output_dir
            else:
                if args.neg_instruction is False:
                    instruction = instructor_instruction_mappping[args.task_names[0]]
                else:
                    instruction = neg_instructor_instruction_mappping[args.task_names[0]]
                    output_dir = os.path.join(f'./results/{model_str}_neg_instruction') if args.output_dir is None else args.output_dir
        else:
            instruction = None
            output_dir = os.path.join(f'./results/{model_str}_wo_instruction') if args.output_dir is None else args.output_dir
    else:
        instruction = None

    evaluation.run(
        model,
        eval_splits=['test'],
        output_folder=output_dir,
        batch_size=args.batch_size,
        output_dir=output_dir,
        save_predictions=args.save_predictions,
        top_k=args.top_k,
        instruction=instruction,
    )

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"The search took {elapsed_time:.6f} seconds to run.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default=None, type=str, required=True)
    parser.add_argument("--model_class", default=None, type=str)
    parser.add_argument("--output_dir", default=None, type=str)
    parser.add_argument("--batch_size", default=16, type=int)
    parser.add_argument("--fp_options", default="bfloat16", type=str) # only for cross encoder
    parser.add_argument("--task_names", default=None, type=str, nargs='+', required=True)
    parser.add_argument("--save_predictions", action='store_false', default=True)
    parser.add_argument("--top_k", default=10, type=int)
    parser.add_argument("--checkpoint_dir", default=None, type=str)
    parser.add_argument("--no_instruction", default=False, type=bool)
    parser.add_argument("--neg_instruction", default=False, type=bool)
    args = parser.parse_args()
    main(args)