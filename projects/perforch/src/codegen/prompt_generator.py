def get_LLM_refine_prompt(problem_data: dict, language: str, function_code: str, overhead_analysis: dict) -> str:
    """
    Constructs a prompt for optimizing code by filling in details from a problem.

    :param problem_data: The problem data dictionary.
    :param language: The programming language.
    :param function_code: The code to optimize. (function header + function body)
    :param overhead_analysis: Overhead metrics dict.
    :return: A formatted prompt string.
    """
    task_description = problem_data.get("docstring", "")
    example_test = problem_data.get("example_test", "")
    prompt_prefix = problem_data.get("prompt", "")

    metrics = overhead_analysis or {}
    execution_time = metrics.get("execution_time")
    max_memory = metrics.get("max_memory")
    overhead_prompt = "\n".join(
        (
            f"The total execution time is: "
            f"{f'{execution_time} ms.' if execution_time is not None else 'Time out.'}",
            f"The maximum memory peak requirement is: "
            f"{f'{max_memory} KB.' if max_memory is not None else 'Out of memory.'}",
        )
    )

    return f"""
Optimize the efficiency of the following {language} code based on the task, test case, and overhead analysis provided. 
Ensure the optimized code can pass the given test case.

Task Description:
{task_description}

Test Case:
{example_test}

Original Code:
```{language}
{prompt_prefix}
{function_code}
```

Overhead Analysis:
{overhead_prompt}

Optimization Rules:
- Focus solely on code optimization.
- Encapsulate the code within a {language} code block (i.e., ```{language}\n[Your Code Here]\n```).
- *Do not* include the test case within the code block.
- Ensure the provided test case passes with your solution.
- Implement *all logic* strictly *within a single method*. 
    - *Do not* split code into multiple methods, helper functions, or classes for any reason. 
    - There should be *only one method* in your implementation.
- *Do not* change the function signature.

Optimized Code:
```{language}
{prompt_prefix}
"""

def get_LLM_fix_prompt(problem_data: dict, language: str, function_code: str) -> str:
    """
    Constructs a prompt for fixing code based on task description and buggy solution.

    :param problem_data: The problem data dictionary.
    :param language: The programming language.
    :param function_code: The buggy function code to fix.
    :return: A formatted prompt string.
    """
    code = function_code
    
    prompt = f"""
Please fix the following code:
```{language}
{problem_data.get('prompt')}
{code}
"""
    return prompt

def get_LLM_generate_prompt(problem_data: dict, language: str) -> str:
    """
    Constructs a prompt for generating code based on task description and test cases.

    :param problem_data: The problem data dictionary.
    :param language: The programming language.
    :return: A formatted prompt string.
    """
    task_description = problem_data.get("docstring")
    example_test = problem_data.get("example_test")

    prompt = f"""
Please complete {language} code `{problem_data.get('signature')}` based on the task description and test cases. 

Task Description:
{task_description}

Test Case:
{example_test}

Rules:
- Encapsulate the code within a {language} code block (i.e., ```{language}\n[Your Code Here]\n```).
- *Do not* include the test case within the code block.
- Ensure the provided test case passes with your solution.
- Implement *all logic* strictly *within a single method*. 
    - *Do not* split code into multiple methods, helper functions, or classes for any reason. 
    - There should be *only one method* in your implementation.
- *Do not* change the function signature.

Solution Code:
```{language}
{problem_data.get('prompt')}
"""
    return prompt 
