"""Functional tests for PerfOrch's benchmark code assembler.

``codegen/full_code_generator.py`` turns a benchmark problem plus a candidate
function body into a complete, compilable program. It has no module-level
imports beyond the standard library and is fully deterministic, so it is
exercised directly.

The Go path is covered through ``get_go_header``/``get_go_foot`` rather than
``generate_full_code`` because the latter shells out to the ``goimports``
binary, whose presence varies between machines.
"""

from __future__ import annotations

import pytest

from codegen.full_code_generator import (
    IMPORT_HELPER,
    _get_function_closing,
    _normalize_language,
    generate_full_code,
    get_cpp_header,
    get_go_foot,
    get_go_header,
    get_java_header,
    get_python_header,
    get_rust_foot,
    get_rust_header,
    modify_function_header,
)


class TestLanguageNormalisation:
    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("python3", "python"),
            ("Python3", "python"),
            ("golang", "go"),
            ("Go", "go"),
            ("CPP", "cpp"),
            ("rust", "rust"),
        ],
    )
    def test_aliases_collapse_to_canonical_names(self, given, expected):
        assert _normalize_language(given) == expected


class TestFunctionClosing:
    @pytest.mark.parametrize(
        ("benchmark", "language", "expected"),
        [
            ("effibenchx", "java", "}"),
            ("effibenchx", "rust", "}"),
            ("effibenchx", "cpp", "};"),
            ("effibenchx", "python", ""),
            ("effibenchx", "go", ""),
            ("humanevalpack", "java", "}"),
            ("humanevalpack", "cpp", ""),
            ("humanevalpack", "python", ""),
        ],
    )
    def test_closing_token_depends_on_benchmark_and_language(self, benchmark, language, expected):
        # C++ needs `};` because EffiBenchX wraps solutions in a class body,
        # whereas Java and Rust close a plain block.
        assert _get_function_closing(benchmark, language) == expected


class TestModifyFunctionHeader:
    def test_drops_the_signature_line_and_keeps_the_body(self):
        definition = "def is_happy(s):\n    return True\n"

        assert modify_function_header(definition) == "    return True"

    def test_blank_lines_are_removed_before_the_signature_is_dropped(self):
        definition = "\n\ndef f(x):\n\n    return x\n\n"

        # The two leading blank lines must not be mistaken for the signature.
        assert modify_function_header(definition) == "    return x"


class TestHeaders:
    def test_python_header_prepends_the_full_import_helper(self):
        header = get_python_header("def solve():")

        assert header.endswith("def solve():")
        assert "import heapq" in header
        assert "sys.setrecursionlimit(1000000)" in header

    def test_cpp_header_omits_includes_already_present_in_the_prompt(self):
        prompt = "#include <vector>\nint solve();"
        header = get_cpp_header(prompt)

        # `#include <vector>` appears once (from the prompt), not twice.
        assert header.count("#include <vector>") == 1
        assert "#include <algorithm>" in header
        assert "using namespace std;" in header

    def test_java_header_prepends_java_imports(self):
        header = get_java_header("class Solution {}")

        assert "import java.util.*;" in header
        assert header.endswith("class Solution {}")

    def test_go_header_emits_a_single_import_block_and_package_main(self):
        header = get_go_header("func solve() {}")

        assert header.startswith("package main\n")
        assert header.count("import (") == 1
        for package in IMPORT_HELPER["go"]:
            assert f'    "{package}"' in header

    def test_rust_header_strips_a_duplicate_main_for_humanevalpack(self):
        prompt = "fn main(){}\nfn solve() -> i32 { 1 }"
        header = get_rust_header(prompt, "humanevalpack")

        # `get_rust_foot` re-adds `fn main`, so the prompt's copy must go.
        assert "fn main(){}" not in header
        assert "fn solve() -> i32 { 1 }" in header

    def test_rust_header_adds_imports_for_effibenchx(self):
        header = get_rust_header("fn solve() {}", "effibenchx")

        assert "use std::collections::" in header
        assert "struct Solution;" in header


class TestFeet:
    def test_go_foot_rewrites_assert_to_require(self):
        assert get_go_foot("assert.Equal(t, 1, 1)") == "require.Equal(t, 1, 1)"

    def test_go_foot_tolerates_a_missing_test_section(self):
        assert get_go_foot(None) == ""

    def test_rust_foot_lifts_the_test_body_into_fn_main(self):
        test = (
            "#[cfg(test)]\n"
            "mod tests {\n"
            "    #[test]\n"
            "    fn test_solve() {\n"
            "        assert_eq!(solve(), 1);\n"
            "    }\n"
            "}\n"
        )
        foot = get_rust_foot(test)

        assert foot.startswith("fn main() {")
        assert foot.rstrip().endswith("}")
        assert "assert_eq!(solve(), 1);" in foot
        # The harness deliberately drops #[cfg(test)] scaffolding.
        assert "#[test]" not in foot
        assert "mod tests" not in foot

    def test_rust_foot_dedents_the_lifted_body_by_one_level(self):
        test = "fn test_solve() {\n        assert_eq!(1, 1);\n}\n"
        foot = get_rust_foot(test)

        assert "\n    assert_eq!(1, 1);" in foot

    def test_rust_foot_raises_when_no_test_function_is_present(self):
        with pytest.raises(Exception, match="No test function found"):
            get_rust_foot("fn helper() {\n    ()\n}\n")


class TestGenerateFullCode:
    def test_python_program_is_header_plus_body_plus_test(self):
        item = {"prompt": "def solve(n):", "test": "assert solve(1) == 1"}
        code = generate_full_code(item, "python", "def solve(n):\n    return n", "humanevalpack")

        assert "import heapq" in code
        assert "def solve(n):" in code
        assert "    return n" in code
        assert code.rstrip().endswith("assert solve(1) == 1")

    def test_canonical_solution_is_used_verbatim(self):
        item = {
            "prompt": "def solve(n):",
            "test": "assert solve(1) == 1",
            "canonical_solution": "    return n",
        }
        code = generate_full_code(item, "python", "canonical_solution", "humanevalpack")

        assert "    return n" in code

    def test_effibenchx_drops_the_prompt_for_canonical_solutions(self):
        item = {
            "prompt": "SENTINEL_PROMPT_TEXT",
            "test": "assert True",
            "canonical_solution": "def solve():\n    return 1",
        }
        code = generate_full_code(item, "python", "canonical_solution", "effibenchx")

        # EffiBenchX canonical solutions already contain the prompt.
        assert "SENTINEL_PROMPT_TEXT" not in code

    def test_effibenchx_java_renames_testsolution_to_main(self):
        item = {"prompt": "class TestSolution {", "test": "// TestSolution runner"}
        code = generate_full_code(item, "java", "public int solve() {\n    return 1;", "effibenchx")

        # The compiled file is Main.java, so the class must be Main.
        assert "TestSolution" not in code
        assert "class Main {" in code

    def test_java_body_is_closed_with_a_brace(self):
        # Upstream contract: `prompt` already ends with the method signature and
        # `function_definition` repeats it, so `modify_function_header` drops the
        # duplicate. The generator then appends the `}` that closes the method,
        # while the benchmark `test` string closes the class.
        item = {"prompt": "class Solution {\n    public int solve() {", "test": "}"}
        code = generate_full_code(item, "java", "public int solve() {\n        return 1;", "humanevalpack")

        assert code.count("{") == 2
        assert code.count("}") == 2
        assert "        return 1;" in code

    def test_generation_failure_returns_an_empty_string(self):
        # Upstream swallows errors and signals failure with "" rather than
        # raising; the pipeline relies on that contract.
        assert generate_full_code({}, "python", "def solve():\n    pass", "humanevalpack") == ""
