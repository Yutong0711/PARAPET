"""End-to-end smoke tests for PerfOrch's Python runtime backend.

These are the only tests in the suite that actually execute generated code.
``python_processor.correctness_test`` writes a candidate to ``main.py`` in a
temporary directory, runs it under the ``timeout`` utility in a fresh process
group, and reports pass/fail plus captured output. That loop -- "write a
candidate, run it on a real workload, record what happened" -- is the middle of
the PARAPET hardening loop and the part the README describes as already
working, so it is worth executing rather than mocking.

Requirements: a POSIX ``timeout`` binary and a writable temp directory. No
network, no GPU, no credentials, no model access.
"""

from __future__ import annotations

import shutil

import pytest

from runtime_processors import python_processor

pytestmark = pytest.mark.skipif(
    shutil.which("timeout") is None,
    reason="PerfOrch's runner shells out to the POSIX `timeout` utility",
)

TIMEOUT_SECONDS = 30


class TestCorrectnessTest:
    def test_a_passing_candidate_is_reported_as_passed(self, tmp_path):
        code = "def solve(n):\n    return n * 2\n\nassert solve(3) == 6\nprint('OK')\n"

        result = python_processor.correctness_test(code, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is True
        assert "OK" in result.logs

    def test_the_candidate_is_written_to_main_py(self, tmp_path):
        code = "print('written')\n"

        python_processor.correctness_test(code, str(tmp_path), TIMEOUT_SECONDS)

        assert (tmp_path / "main.py").read_text(encoding="utf-8") == code

    def test_a_failing_assertion_is_reported_as_not_passed(self, tmp_path):
        code = "def solve(n):\n    return n\n\nassert solve(3) == 6\n"

        result = python_processor.correctness_test(code, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is False
        assert "AssertionError" in result.logs

    def test_a_syntax_error_is_reported_as_not_passed(self, tmp_path):
        result = python_processor.correctness_test("def broken(\n", str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is False
        assert "SyntaxError" in result.logs

    def test_a_nonzero_exit_is_reported_as_not_passed(self, tmp_path):
        result = python_processor.correctness_test("import sys\nsys.exit(3)\n", str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is False

    def test_an_overrunning_candidate_is_killed_by_the_timeout(self, tmp_path):
        code = "import time\ntime.sleep(30)\n"

        result = python_processor.correctness_test(code, str(tmp_path), 1)

        # The runner must bound execution; without this a single pathological
        # candidate would stall the whole benchmark sweep.
        assert result.passed is False

    def test_stdout_and_stderr_are_both_captured(self, tmp_path):
        code = "import sys\nsys.stdout.write('out-marker\\n')\nsys.stderr.write('err-marker\\n')\n"

        result = python_processor.correctness_test(code, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is True
        assert "out-marker" in result.logs
        assert "err-marker" in result.logs

    def test_no_timing_or_memory_is_recorded_by_a_correctness_run(self, tmp_path):
        result = python_processor.correctness_test("print(1)\n", str(tmp_path), TIMEOUT_SECONDS)

        # Cost numbers come from the profiling pass, never the correctness pass.
        assert result.execution_time_all is None
        assert result.max_memory is None
        assert result.average_memory is None


class TestWrappedCandidateStillRuns:
    def test_a_marker_wrapped_candidate_executes_the_body_n_times(self, tmp_path):
        code = (
            "import pathlib\n"
            "counter = pathlib.Path('runs.txt')\n"
            "def solve():\n"
            "    counter.write_text(str(int(counter.read_text() or 0) + 1))\n"
            "counter.write_text('0')\n"
            "# Test cases\n"
            "solve()\n"
        )

        wrapped = python_processor.wrap_py(code, 4)
        result = python_processor.correctness_test(wrapped, str(tmp_path), TIMEOUT_SECONDS)

        # The wrap transformation and the runner have to agree: the loop must
        # be syntactically valid and actually repeat the workload.
        assert result.passed is True, result.logs
        assert (tmp_path / "runs.txt").read_text(encoding="utf-8") == "4"
