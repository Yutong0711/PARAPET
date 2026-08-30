"""Functional tests for PerfOrch's per-language runtime processors.

Each processor owns two things: a ``wrap_*`` source transformation that repeats
the benchmark body N times so a runtime measurement is large enough to be
meaningful, and a ``correctness_test``/``refine_test`` pair built from
``core.build_processor_api``.

The ``wrap_*`` functions are pure and deterministic and are tested directly.
The registry is tested because the pipeline dispatches on it for every
candidate, so a missing or misnamed backend silently loses a language.

These tests import ``runtime_processors.core``, which imports numpy; nothing
here compiles or executes generated code (see ``test_python_runtime.py`` and
``test_java_runtime.py`` for that).
"""

from __future__ import annotations

import pytest

from runtime_processors import (
    cpp_processor,
    go_processor,
    java_processor,
    python_processor,
    rust_processor,
)
from runtime_processors.registry import SUPPORTED_LANGUAGES, get_processor


class TestRegistry:
    def test_all_five_advertised_languages_are_registered(self):
        # PARAPET's README and site both claim C++, Go, Java, Python and Rust.
        assert set(SUPPORTED_LANGUAGES) == {"cpp", "go", "java", "python", "rust"}

    @pytest.mark.parametrize(
        ("language", "module"),
        [
            ("cpp", cpp_processor),
            ("go", go_processor),
            ("java", java_processor),
            ("python", python_processor),
            ("rust", rust_processor),
        ],
    )
    def test_each_language_resolves_to_its_own_backend(self, language, module):
        assert get_processor(language) is module

    def test_lookup_is_case_insensitive(self):
        assert get_processor("Python") is python_processor
        assert get_processor("CPP") is cpp_processor

    def test_unknown_language_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            get_processor("haskell")

    @pytest.mark.parametrize("language", ["cpp", "go", "java", "python", "rust"])
    def test_every_backend_exposes_the_processor_api(self, language):
        processor = get_processor(language)

        assert callable(processor.correctness_test)
        assert callable(processor.refine_test)


class TestPythonWrapping:
    def test_the_test_cases_marker_is_wrapped_and_the_body_indented(self):
        code = "def solve():\n    return 1\n# Test cases\nassert solve() == 1\n"

        wrapped = python_processor.wrap_py(code, 5)

        assert "for warp in range(5):" in wrapped
        assert "    assert solve() == 1" in wrapped
        # Everything before the marker keeps its original indentation.
        assert wrapped.startswith("def solve():\n    return 1\n# Test cases\n")

    def test_blank_lines_after_the_marker_are_not_indented(self):
        code = "# Test cases\n\nassert True\n"

        wrapped = python_processor.wrap_py(code, 2)
        lines = wrapped.split("\n")

        assert "" in lines

    def test_a_check_call_is_wrapped_when_no_marker_is_present(self):
        code = "def solve():\n    return 1\ncheck(solve)\n"

        wrapped = python_processor.wrap_py(code, 3)

        assert "for warp in range(3):" in wrapped
        assert "    check(solve)" in wrapped

    def test_code_with_neither_marker_nor_check_is_returned_unchanged(self):
        code = "print('hello')\n"

        assert python_processor.wrap_py(code, 10) == code

    def test_the_marker_takes_priority_over_a_check_call(self):
        code = "# Test cases\ncheck(solve)\n"

        wrapped = python_processor.wrap_py(code, 4)

        # Only one loop is inserted, from the marker branch.
        assert wrapped.count("for warp in range(4):") == 1


class TestJavaWrapping:
    def test_the_main_body_is_wrapped_in_a_counted_loop(self):
        code = (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(1);\n"
            "    }\n"
            "}\n"
        )

        wrapped = java_processor.wrap_java(code, 7)

        assert "for (int warp = 0; warp < 7; warp++) {" in wrapped
        assert "System.out.println(1);" in wrapped
        assert wrapped.count("{") == wrapped.count("}")

    def test_code_without_a_main_is_rejected(self):
        with pytest.raises(ValueError, match="No valid main function found"):
            java_processor.wrap_java("public class Main {\n}\n", 3)


class TestCppWrapping:
    def test_the_main_body_is_wrapped_and_the_return_hoisted_out(self):
        code = (
            "int main() {\n"
            "    compute();\n"
            "    return 0;\n"
            "}\n"
        )

        wrapped = cpp_processor.wrap_cpp(code, 9)
        lines = [line.strip() for line in wrapped.split("\n") if line.strip()]

        assert "for (int warp = 0; warp < 9; warp++) {" in wrapped
        # `return 0;` must sit after the loop's closing brace, not inside it,
        # or the benchmark would exit on the first iteration.
        assert lines == [
            "int main() {",
            "for (int warp = 0; warp < 9; warp++) {",
            "compute();",
            "}",
            "return 0;",
            "}",
        ]

    def test_code_without_a_main_is_rejected(self):
        with pytest.raises(ValueError, match="No valid main function found"):
            cpp_processor.wrap_cpp("void helper() {\n}\n", 2)


class TestRustWrapping:
    def test_the_main_body_is_wrapped_in_a_counted_loop(self):
        code = "fn main() {\n    compute();\n}\n"

        wrapped = rust_processor.wrap_rs(code, 6)

        assert "for _warp in 0..6 {" in wrapped
        assert "compute();" in wrapped

    def test_code_without_a_main_is_rejected(self):
        with pytest.raises(ValueError, match="No valid main function found"):
            rust_processor.wrap_rs("fn helper() {\n}\n", 2)


class TestGoWrapping:
    def test_the_test_function_body_is_wrapped_except_its_closing_brace(self):
        code = (
            "package main\n"
            "func TestSolve(t *testing.T) {\n"
            "\trequire.Equal(t, 1, solve())\n"
            "}\n"
        )

        wrapped = go_processor.wrap_go(code, 8)

        assert "for warp := 0; warp < 8; warp++ {" in wrapped
        assert "require.Equal(t, 1, solve())" in wrapped
        assert wrapped.count("{") == wrapped.count("}")

    def test_code_without_a_test_function_is_returned_unchanged(self):
        code = "package main\nfunc main() {}\n"

        assert go_processor.wrap_go(code, 5) == code

    def test_post_write_hook_rewrites_assert_to_require(self, tmp_path):
        source = tmp_path / "main_test.go"
        source.write_text("assert.Equal(t, 1, 1)\n", encoding="utf-8")

        go_processor.replace_assert_with_require(str(source))

        assert source.read_text(encoding="utf-8") == "require.Equal(t, 1, 1)\n"


class TestProcessorConfiguration:
    def test_the_python_backend_runs_the_current_interpreter(self):
        # Guards against the harness silently benchmarking a different Python
        # from the one running the pipeline.
        import sys

        assert python_processor.PYTHON_BIN == sys.executable
