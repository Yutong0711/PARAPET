import tempfile

from runtime_processors.core import (
    BASE_RUN_TIMES,
    BENCHMARK_RUN_TIMES,
    CORRECTNESS_TIMEOUT,
    PROFILE_TIMEOUT,
    setup_environment,
)
from runtime_processors.registry import get_processor
from codegen.function_extractor import (
    FunctionExtractorError,
    extract_function_by_language,
)
from llm_generator import generate_text
from codegen.prompt_generator import (
    get_LLM_fix_prompt,
    get_LLM_generate_prompt,
    get_LLM_refine_prompt,
)


def evaluate_candidate(language: str, name: str, full_code: str, test_type: str = "full", benchmark: str = ""):
    """
    Evaluate candidate code for correctness and optionally performance.

    :param test_type: "correctness" runs correctness checks only;
        "full" runs correctness checks and profiling.
    """
    language = language.lower()
    if test_type not in {"correctness", "full"}:
        raise ValueError(f"Unsupported test_type: {test_type}")

    need_profile = test_type == "full"
    data = {
        "passed": False,
        "execution_time": None,
        "max_memory": None,
        "average_memory": None,
        "cpus_utilized": None,
    }

    with tempfile.TemporaryDirectory(prefix=f"tmp_{name.replace('/', '_')}_") as temp_dir:
        setup_environment(language, temp_dir)
        processor = get_processor(language)

        try:
            correctness_res = processor.correctness_test(full_code, temp_dir, CORRECTNESS_TIMEOUT)
            data["passed"] = correctness_res.passed
        except Exception:
            return data

        if (not need_profile) or (not data["passed"]):
            return data

        try:
            run_times = BENCHMARK_RUN_TIMES.get(benchmark, BASE_RUN_TIMES)
            profile_res = processor.refine_test(run_times, temp_dir, PROFILE_TIMEOUT)
        except Exception:
            data["passed"] = False
            return data

        data.update(
            passed=profile_res.passed,
            max_memory=profile_res.max_memory,
            average_memory=profile_res.average_memory,
            cpus_utilized=profile_res.cpus_utilized,
        )

        if not data["passed"]:
            return data

        execution_time = profile_res.execution_time_all
        if execution_time is None:
            data["passed"] = False
            return data

        data["execution_time"] = execution_time
        return data


def run_llm_function_op(
    problem_data: dict,
    language: str,
    model_name: str,
    operation: str,
    input_function_code: str = None,
    overhead_analysis: dict = None,
    temperature: float = None,
    top_p: float = None,
):
    """
    Process a single task and return function-definition level results.

    Supports three operations: fix, generate, and refine.

    :param input_function_code: Function source code to process
        (required for fix and refine).
    """
    operation = (operation or "").strip().lower()
    function_name = problem_data.get("entry_point")
    name = problem_data.get("task_id")
    function_before = input_function_code if operation in {"fix", "refine"} else None
    if not isinstance(function_name, str) or not function_name.strip():
        raise ValueError(f"Missing entry_point: task={name}")

    if operation not in {"fix", "generate", "refine"}:
        raise ValueError(f"Unsupported operation: {operation}")
    if operation in {"fix", "refine"} and not (function_before or "").strip():
        raise ValueError(f"input_function_code is required for operation={operation}")

    if operation == "generate":
        llm_input = get_LLM_generate_prompt(problem_data, language)
    elif operation == "fix":
        llm_input = get_LLM_fix_prompt(problem_data, language, function_before)
    else:
        llm_input = get_LLM_refine_prompt(
            problem_data,
            language,
            function_before,
            overhead_analysis or {},
        )

    result = generate_text(llm_input, model_name, temperature=temperature, top_p=top_p)
    if not isinstance(result, dict):
        raise RuntimeError(
            f"LLM call returned invalid response type: task={name}, model={model_name}, "
            f"op={operation}, type={type(result).__name__}"
        )
    if result.get("status") != "success":
        raise RuntimeError(
            f"LLM call failed: task={name}, model={model_name}, op={operation}, "
            f"error={result.get('error')}"
        )

    llm_output = result.get("text") or ""
    if not llm_output.strip():
        raise RuntimeError(
            f"LLM returned empty output: task={name}, model={model_name}, op={operation}"
        )

    try:
        function_after = extract_function_by_language(language, llm_output, function_name)
    except FunctionExtractorError:
        # Fallback keeps pipeline robust for imperfect LLM formatting.
        function_after = llm_output
    if not function_after.strip():
        raise RuntimeError(
            f"Function extraction produced empty code: task={name}, model={model_name}, op={operation}"
        )

    return {
        "task_id": name,
        "LLM_input": llm_input,
        "LLM_output": llm_output,
        "function_before": function_before,
        "function_after": function_after,
    }
