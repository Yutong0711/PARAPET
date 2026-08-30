"""Functional tests for PerfOrch's multi-language function extractor.

``codegen/function_extractor.py`` is the component that turns raw model output
into a single compilable function body. It is pure, stdlib-only and
deterministic, so it is tested directly against real source snippets.

The PARAPET site claims PerfOrch "compiles and runs them across C++, Go, Java,
Python, and Rust"; these tests cover the extraction half of that claim for all
five languages.
"""

from __future__ import annotations

import pytest

from codegen.function_extractor import (
    FunctionExtractorError,
    extract_cpp_function,
    extract_function_by_language,
    extract_go_function,
    extract_java_function,
    extract_python_function,
    extract_rust_function,
)


class TestPythonExtraction:
    def test_extracts_only_the_named_function(self):
        source = (
            "def helper(x):\n"
            "    return x + 1\n"
            "\n"
            "def target(a, b):\n"
            "    total = a + b\n"
            "    return total\n"
            "\n"
            "def trailing(y):\n"
            "    return y\n"
        )
        extracted = extract_python_function(source, "target")

        assert extracted.startswith("def target(a, b):")
        assert "total = a + b" in extracted
        # Neighbouring definitions must not leak in.
        assert "def helper" not in extracted
        assert "def trailing" not in extracted

    def test_stops_at_a_markdown_fence(self):
        source = (
            "def target():\n"
            "    return 1\n"
            "```\n"
            "def not_code():\n"
            "    return 2\n"
        )
        extracted = extract_python_function(source, "target")

        assert "not_code" not in extracted
        assert "```" not in extracted

    def test_tabs_are_normalised_to_spaces(self):
        source = "def target(a):\n\treturn a\n"
        extracted = extract_python_function(source, "target")

        assert "\t" not in extracted
        assert extracted == "def target(a):\n    return a"

    def test_return_annotation_in_signature_is_matched(self):
        source = "def target(a: int) -> list[int]:\n    return [a]\n"
        extracted = extract_python_function(source, "target")

        assert extracted.startswith("def target(a: int) -> list[int]:")

    def test_definition_named_only_inside_a_comment_is_ignored(self):
        source = (
            "# def target(): never defined\n"
            "def other():\n"
            "    return 0\n"
        )
        with pytest.raises(FunctionExtractorError):
            extract_python_function(source, "target")

    def test_missing_function_raises_with_the_name_in_the_message(self):
        with pytest.raises(FunctionExtractorError) as excinfo:
            extract_python_function("def other():\n    pass\n", "target")

        assert "target" in str(excinfo.value)


class TestBraceLanguageExtraction:
    def test_cpp_balances_braces_across_nested_blocks(self):
        source = (
            "#include <vector>\n"
            "int target(int n) {\n"
            "    if (n > 0) {\n"
            "        return n;\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
            "int after() { return 1; }\n"
        )
        extracted = extract_cpp_function(source, "target")

        assert extracted.count("{") == extracted.count("}")
        assert "return 0;" in extracted
        assert "after" not in extracted

    def test_cpp_ignores_a_call_inside_a_block_comment(self):
        source = (
            "/* target(1) is documented here */\n"
            "int target(int n) {\n"
            "    return n;\n"
            "}\n"
        )
        extracted = extract_cpp_function(source, "target")

        assert extracted.splitlines()[0].strip().startswith("int target(int n)")

    def test_java_requires_a_public_modifier(self):
        source = (
            "class Solution {\n"
            "    private int target(int n) {\n"
            "        return n;\n"
            "    }\n"
            "}\n"
        )
        with pytest.raises(FunctionExtractorError):
            extract_java_function(source, "target")

    def test_java_extracts_a_public_method(self):
        source = (
            "class Solution {\n"
            "    public int target(int n) {\n"
            "        return n * 2;\n"
            "    }\n"
            "}\n"
        )
        extracted = extract_java_function(source, "target")

        assert "public int target(int n)" in extracted
        assert "return n * 2;" in extracted
        assert extracted.count("{") == extracted.count("}")

    def test_go_extracts_a_func_declaration(self):
        source = (
            "package main\n"
            "\n"
            "func target(n int) int {\n"
            "    return n\n"
            "}\n"
        )
        extracted = extract_go_function(source, "target")

        assert extracted.startswith("func target(n int) int {")
        assert extracted.rstrip().endswith("}")

    def test_rust_requires_the_fn_keyword_before_the_name(self):
        source = (
            "fn caller() {\n"
            "    target(1);\n"
            "}\n"
            "fn target(n: i32) -> i32 {\n"
            "    n\n"
            "}\n"
        )
        extracted = extract_rust_function(source, "target")

        # The bare call `target(1)` inside `caller` must not be mistaken for the
        # definition -- only `fn target(` counts.
        assert extracted.startswith("fn target(n: i32) -> i32 {")
        assert "caller" not in extracted

    def test_allman_brace_style_returns_signature_only_known_limitation(self):
        """Characterises a real upstream limitation of the brace extractor.

        ``_has_brace_in_signature_or_next`` accepts a function whose opening
        brace is on the *next* line, so the definition is located. But
        ``_extract_brace_block`` starts its brace count on the signature line,
        which is already balanced at zero, so it stops immediately and returns
        the signature alone. Allman-style C/C++ output is therefore truncated.

        This is upstream PerfOrch behaviour and is deliberately NOT patched
        here -- vendored research code is not rewritten to make tests pass. The
        test is pinned so that a future upstream fix shows up as a change
        instead of passing silently.
        """
        source = (
            "int target(int n)\n"
            "{\n"
            "    return n;\n"
            "}\n"
        )
        extracted = extract_cpp_function(source, "target")

        assert extracted == "int target(int n)"
        assert "return n;" not in extracted


class TestLanguageDispatch:
    @pytest.mark.parametrize(
        ("language", "source", "expected_fragment"),
        [
            ("python", "def target(a):\n    return a\n", "def target(a):"),
            ("cpp", "int target() {\n    return 1;\n}\n", "int target()"),
            ("java", "public int target() {\n    return 1;\n}\n", "public int target()"),
            ("go", "func target() int {\n    return 1\n}\n", "func target() int"),
            ("rust", "fn target() -> i32 {\n    1\n}\n", "fn target() -> i32"),
        ],
    )
    def test_every_supported_language_dispatches(self, language, source, expected_fragment):
        assert expected_fragment in extract_function_by_language(language, source, "target")

    def test_language_name_is_case_insensitive(self):
        extracted = extract_function_by_language("PYTHON", "def target():\n    return 1\n", "target")

        assert extracted.startswith("def target():")

    def test_unsupported_language_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported language"):
            extract_function_by_language("haskell", "target = 1", "target")
