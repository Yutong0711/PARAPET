"""Functional tests for the More Than Just Functional profiler transform.

``projects/more-than-just-functional/src/util.py`` contains the artifact's
AST pass: given a generated solution plus its assert-based tests, it recovers
the target function name, decodes the literal test cases, and injects a
``@profile`` decorator so time or memory can be measured. It is stdlib-only
(``ast``) and deterministic.

The artifact's *experiments* need transformers and CUDA and are not runnable
here; this transformation is the part that is self-contained, and it is the
mechanism behind the "multi-candidate generate-and-critique" drafting workflow
the README cites.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

from util import extract_assert_tests_and_add_profiler, extract_constant


def _const(expression):
    """Parse a literal expression and hand the AST node to extract_constant."""
    return extract_constant(ast.parse(expression, mode="eval").body)


class TestExtractConstant:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            ("42", 42),
            ("'text'", "text"),
            ("True", True),
            ("None", None),
            ("3.5", 3.5),
            ("[1, 2, 3]", [1, 2, 3]),
            ("(1, 'a')", (1, "a")),
            ("{'k': 1}", {"k": 1}),
            ("{1, 2}", {1, 2}),
            ("[[1, 2], [3]]", [[1, 2], [3]]),
            ("{'k': [1, {'n': 2}]}", {"k": [1, {"n": 2}]}),
        ],
    )
    def test_literal_structures_are_decoded(self, source, expected):
        assert _const(source) == expected

    @pytest.mark.parametrize(("source", "expected"), [("-1", -1), ("+2", 2), ("not True", False)])
    def test_unary_operators_are_evaluated(self, source, expected):
        assert _const(source) == expected

    def test_nested_negative_numbers_inside_a_list_are_decoded(self):
        assert _const("[-1, [-2]]") == [-1, [-2]]

    def test_a_name_reference_is_rejected_rather_than_silently_dropped(self):
        # Test cases must be literals; a variable reference cannot be replayed.
        with pytest.raises(ValueError):
            _const("some_variable")

    def test_an_unsupported_unary_operator_is_rejected(self):
        with pytest.raises(ValueError):
            _const("~1")


class TestExtractAssertTestsAndAddProfiler:
    SOURCE = textwrap.dedent(
        """
        class Solution:
            def two_sum(self, nums, target):
                return [0, 1]

        s = Solution()
        assert s.two_sum([2, 7], 9) == [0, 1]
        assert s.two_sum([3, 3], 6) == [0, 1]
        """
    )

    def test_the_target_function_is_recovered_from_the_asserts(self):
        _, _, target = extract_assert_tests_and_add_profiler(self.SOURCE)

        assert target == "two_sum"

    def test_every_assert_becomes_a_replayable_test_case(self):
        _, cases, _ = extract_assert_tests_and_add_profiler(self.SOURCE)

        assert cases == [
            {"input": [[2, 7], 9], "expected": [0, 1]},
            {"input": [[3, 3], 6], "expected": [0, 1]},
        ]

    def test_the_time_profiler_is_injected_as_a_bare_decorator(self):
        code, _, _ = extract_assert_tests_and_add_profiler(self.SOURCE, profile_type="time")

        assert "@profile\n" in code
        # The transformed source must still parse and still contain the body.
        assert ast.parse(code)
        assert "return [0, 1]" in code

    def test_the_memory_profiler_is_injected_with_stream_and_precision(self):
        code, _, _ = extract_assert_tests_and_add_profiler(self.SOURCE, profile_type="memory")

        assert "@profile(stream=profile_stream, precision=PROFILE_PRECISION)" in code
        assert ast.parse(code)

    def test_only_the_target_function_is_decorated(self):
        source = textwrap.dedent(
            """
            class Solution:
                def helper(self, x):
                    return x
                def target(self, x):
                    return self.helper(x)

            s = Solution()
            assert s.target(1) == 1
            """
        )

        code, _, target = extract_assert_tests_and_add_profiler(source)
        tree = ast.parse(code)
        decorated = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.decorator_list
        }

        assert target == "target"
        assert decorated == {"target"}

    def test_source_without_a_method_call_assert_is_rejected(self):
        with pytest.raises(ValueError):
            extract_assert_tests_and_add_profiler("assert 1 == 1\n")

    def test_an_unsupported_profile_type_exits_rather_than_producing_bad_code(self):
        # Upstream calls sys.exit() here; emitting undecorated code would
        # silently yield a run with no measurement at all.
        with pytest.raises(SystemExit):
            extract_assert_tests_and_add_profiler(self.SOURCE, profile_type="cpu")
