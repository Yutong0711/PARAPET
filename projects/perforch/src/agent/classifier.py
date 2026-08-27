from typing import Optional
from llm_generator import generate_text
from .utils import lookup_categories_by_id

CATEGORIES = [
    "Array",
    "Math",
    "String",
    "Counting",
    "Num Theory",
    "Simulation",
    "Sorting",
    "Enumeration",
    "Greedy",
    "Hash Table"
]

def get_classification_prompt(problem_description: str) -> str:
    """
    Constructs the prompt for classifying a coding problem.

    :param problem_description: The description of the problem.
    :return: The formatted prompt string.
    """
    available_cats = ", ".join(CATEGORIES)

    prompt = f"""
Please classify the following coding problem by assigning the
appropriate categories based on the problem description:
Problem Description : {problem_description}
Available categories : {available_cats}
Please select the appropriate categories from the available categories based on the
nature of the problem .
If the problem is not related to any of the available categories , please
select the closest categories
"""
    return prompt

def classify_problem(
    problem_description: str,
    model_name: str,
    benchmark_task_id: Optional[str] = None,
    benchmark_name: Optional[str] = None
) -> dict:
    """
    Classifies a problem into categories using an LLM.

    :param problem_description: The description of the problem.
    :param model_name: The name of the LLM model to use.
    :return: A dictionary containing 'tags', 'prompt', and 'raw_output'.
    """
    if benchmark_task_id:
        categories = lookup_categories_by_id(benchmark_task_id, benchmark_name)
        if categories:
            return {
                "tags": categories,
                "prompt": None,
                "raw_output": None,
                "source": "benchmark_category",
            }

    prompt = get_classification_prompt(problem_description)
    
    result = {
        "tags": [],
        "prompt": prompt,
        "raw_output": None,
        "source": "llm"
    }
    
    try:
        response = generate_text(prompt, model_name)
        if response["status"] == "success":
            text = response["text"]
            result["raw_output"] = text
            identified_categories = []
            for category in CATEGORIES:
                if category.lower() in text.lower():
                    identified_categories.append(category)
            
            result["tags"] = identified_categories
            return result
        else:
            print(f"Error calling LLM: {response.get('error')}")
            return result
            
    except Exception as e:
        print(f"Error in classify_problem: {e}")
        return result
