"""Functional tests for PerfOrch's prompt construction.

``codegen/prompt_generator.py`` is the boundary between measured runtime data
and the model. Its only real branching is how a *missing* measurement is
described -- a timed-out run must be reported as "Time out." rather than as a
number, and an OOM run as "Out of memory." Getting that wrong would feed a
model a fabricated cost figure, so it is covered explicitly.
"""

from __future__ import annotations

import pytest

from codegen.prompt_generator import (
    get_LLM_fix_prompt,
    get_LLM_generate_prompt,
    get_LLM_refine_prompt,
)

PROBLEM = {
    "docstring": "Return the sum of two integers.",
    "example_test": "assert solve(1, 2) == 3",
    "prompt": "def solve(a, b):",
    "signature": "solve(a, b)",
}


class TestRefinePrompt:
    def test_measured_values_are_reported_with_units(self):
        prompt = get_LLM_refine_prompt(
            PROBLEM, "python", "    return a + b", {"execution_time": 12.5, "max_memory": 2048}
        )

        assert "The total execution time is: 12.5 ms." in prompt
        assert "The maximum memory peak requirement is: 2048 KB." in prompt

    def test_a_missing_execution_time_is_reported_as_a_timeout(self):
        prompt = get_LLM_refine_prompt(
            PROBLEM, "python", "    return a + b", {"execution_time": None, "max_memory": 100}
        )

        # Never invent a number for a run that did not finish.
        assert "The total execution time is: Time out." in prompt
        assert "None ms" not in prompt

    def test_a_missing_memory_reading_is_reported_as_out_of_memory(self):
        prompt = get_LLM_refine_prompt(
            PROBLEM, "python", "    return a + b", {"execution_time": 5.0, "max_memory": None}
        )

        assert "The maximum memory peak requirement is: Out of memory." in prompt
        assert "None KB" not in prompt

    @pytest.mark.parametrize("overhead", [None, {}])
    def test_an_absent_overhead_analysis_degrades_to_both_failure_messages(self, overhead):
        prompt = get_LLM_refine_prompt(PROBLEM, "python", "    return a + b", overhead)

        assert "Time out." in prompt
        assert "Out of memory." in prompt

    def test_the_problem_context_and_candidate_are_both_included(self):
        prompt = get_LLM_refine_prompt(PROBLEM, "python", "    return a + b", {"execution_time": 1.0, "max_memory": 1})

        assert PROBLEM["docstring"] in prompt
        assert PROBLEM["example_test"] in prompt
        assert "    return a + b" in prompt

    @pytest.mark.parametrize("language", ["python", "cpp", "go", "java", "rust"])
    def test_the_code_fence_is_tagged_with_the_target_language(self, language):
        prompt = get_LLM_refine_prompt(PROBLEM, language, "body", {"execution_time": 1.0, "max_memory": 1})

        assert f"```{language}" in prompt


class TestGenerateAndFixPrompts:
    def test_generate_prompt_carries_the_signature_and_test_case(self):
        prompt = get_LLM_generate_prompt(PROBLEM, "python")

        assert PROBLEM["signature"] in prompt
        assert PROBLEM["example_test"] in prompt
        assert PROBLEM["docstring"] in prompt

    def test_fix_prompt_carries_the_buggy_candidate(self):
        prompt = get_LLM_fix_prompt(PROBLEM, "python", "    return a - b")

        assert "    return a - b" in prompt
        assert "```python" in prompt

    def test_missing_optional_problem_fields_do_not_raise(self):
        # Benchmarks differ in which fields they populate; prompt building must
        # not crash on a sparse record.
        prompt = get_LLM_generate_prompt({}, "python")

        assert "```python" in prompt
