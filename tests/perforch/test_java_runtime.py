"""End-to-end smoke tests for PerfOrch's Java runtime backend.

``java_processor`` compiles ``Main.java`` with ``javac`` and runs it with
``java``. This is the only JVM path in the repository -- there is no Maven or
Gradle build -- so these tests exercise it through the processor's own
compile-and-run API rather than through a build tool.

Marked ``jvm`` and skipped when no JDK is on PATH, so the suite still runs on a
machine without Java. CI installs a JDK and runs this job explicitly.
"""

from __future__ import annotations

import shutil

import pytest

from runtime_processors import java_processor

pytestmark = [
    pytest.mark.jvm,
    pytest.mark.skipif(
        shutil.which("javac") is None or shutil.which("java") is None,
        reason="requires a JDK (javac and java) on PATH",
    ),
    pytest.mark.skipif(
        shutil.which("timeout") is None,
        reason="PerfOrch's runner shells out to the POSIX `timeout` utility",
    ),
]

TIMEOUT_SECONDS = 120

HELLO = (
    "public class Main {\n"
    "    public static void main(String[] args) {\n"
    "        System.out.println(\"JAVA-OK\");\n"
    "    }\n"
    "}\n"
)


class TestJavaCorrectnessTest:
    def test_a_valid_program_compiles_runs_and_passes(self, tmp_path):
        result = java_processor.correctness_test(HELLO, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is True, result.logs
        assert "JAVA-OK" in result.logs

    def test_the_candidate_is_written_to_main_java_and_compiled(self, tmp_path):
        java_processor.correctness_test(HELLO, str(tmp_path), TIMEOUT_SECONDS)

        assert (tmp_path / "Main.java").read_text(encoding="utf-8") == HELLO
        assert (tmp_path / "Main.class").exists()

    def test_a_compile_error_is_reported_as_a_compilation_failure(self, tmp_path):
        broken = "public class Main { public static void main(String[] a) { int x = ; } }\n"

        result = java_processor.correctness_test(broken, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is False
        assert "Compilation failed" in result.logs

    def test_a_runtime_exception_is_reported_as_not_passed(self, tmp_path):
        throwing = (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        throw new IllegalStateException(\"boom\");\n"
            "    }\n"
            "}\n"
        )

        result = java_processor.correctness_test(throwing, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is False
        assert "IllegalStateException" in result.logs


class TestWrappedJavaCandidateStillCompiles:
    def test_a_loop_wrapped_program_compiles_and_repeats_the_body(self, tmp_path):
        source = (
            "public class Main {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"TICK\");\n"
            "    }\n"
            "}\n"
        )

        wrapped = java_processor.wrap_java(source, 3)
        result = java_processor.correctness_test(wrapped, str(tmp_path), TIMEOUT_SECONDS)

        # The benchmark-loop transformation has to produce code javac accepts,
        # and the workload has to actually run N times.
        assert result.passed is True, result.logs
        assert result.logs.count("TICK") == 3
