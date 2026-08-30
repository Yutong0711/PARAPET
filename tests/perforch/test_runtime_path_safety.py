"""Regression tests: PerfOrch's runtime must survive spaces in paths.

PARAPET's repository is checked out at a path containing a space
(``/mnt/d/Funding/2026 PESOSE/...``), and a virtualenv created there gives
``sys.executable`` a space too. PerfOrch used to hand its run command to
``run_with_timeout`` as a *shell-syntax string* built by interpolation --
``f"{PYTHON_BIN} main.py"`` -- which ``core.run_with_timeout`` then re-split
with ``shlex.split``. A space in the interpreter path therefore split one
argument into two, and ``timeout`` was asked to execute a prefix of the path:

    timeout: failed to execute process: No such file or directory (os error 2)

That is a silent, total failure of the measurement backend on any checkout
whose path contains a space, so it is guarded here rather than left to the
environment. The fix is argv lists passed straight to ``subprocess`` -- no
shell parsing anywhere in the path -- and these tests fail on the old
string-interpolating implementation.

Requirements: a POSIX ``timeout`` binary, a writable temp directory, and
symlink support. No network, no GPU, no credentials, no model access.
"""

from __future__ import annotations

import os
import shutil
import sys

import pytest

from runtime_processors import core, python_processor

pytestmark = pytest.mark.skipif(
    shutil.which("timeout") is None,
    reason="PerfOrch's runner shells out to the POSIX `timeout` utility",
)

TIMEOUT_SECONDS = 30

PASSING_CANDIDATE = "def solve(n):\n    return n * 2\n\nassert solve(3) == 6\nprint('OK')\n"


@pytest.fixture
def spaced_dir(tmp_path):
    """A working directory whose absolute path contains spaces."""
    path = tmp_path / "a dir with spaces" / "and another one"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def spaced_interpreter(tmp_path):
    """A working Python interpreter reachable only via a path with spaces.

    Symlinks the *resolved* interpreter, so the alias is a real executable
    rather than a venv shim that might not find its own prefix. The candidates
    run through it use nothing but the standard library.
    """
    bin_dir = tmp_path / "py bin dir"
    bin_dir.mkdir()
    alias = bin_dir / "python3"
    try:
        alias.symlink_to(os.path.realpath(sys.executable))
    except (OSError, NotImplementedError) as exc:  # pragma: no cover - platform guard
        pytest.skip(f"cannot symlink an interpreter alias here: {exc}")
    return str(alias)


def _python_api_for(interpreter):
    """Rebuild the Python backend exactly as ``python_processor`` builds it.

    ``build_processor_api`` closes over the command at import time, so pointing
    the backend at a different interpreter means rebuilding it the same way the
    module does rather than patching module state.
    """
    return core.build_processor_api(
        source_relpath="main.py",
        wrap_fn=python_processor.wrap_py,
        compile_fn=None,
        run_cmd=[interpreter, "main.py"],
        memory_cmd=[interpreter, "main.py"],
    )


class TestSpacesInTheWorkingDirectory:
    def test_correctness_test_runs_from_a_directory_whose_path_contains_spaces(self, spaced_dir):
        """The reported failure: this repository lives under a spaced path."""
        result = python_processor.correctness_test(
            PASSING_CANDIDATE, str(spaced_dir), TIMEOUT_SECONDS
        )

        assert result.passed is True, result.logs
        assert "OK" in result.logs

    def test_the_candidate_is_written_into_the_spaced_directory(self, spaced_dir):
        python_processor.correctness_test("print('written')\n", str(spaced_dir), TIMEOUT_SECONDS)

        assert (spaced_dir / "main.py").read_text(encoding="utf-8") == "print('written')\n"

    def test_a_failing_candidate_still_reports_its_error_from_a_spaced_directory(self, spaced_dir):
        """A spaced path must not be misreported as a candidate failure.

        Before the fix every candidate "failed" with an exec error, which would
        have scored a perfectly good patch as broken.
        """
        result = python_processor.correctness_test(
            "assert 1 == 2\n", str(spaced_dir), TIMEOUT_SECONDS
        )

        assert result.passed is False
        assert "AssertionError" in result.logs
        assert "failed to execute process" not in result.logs


class TestSpacesInTheInterpreterPath:
    """Fails on the old implementation wherever the repository is checked out."""

    def test_correctness_test_runs_under_an_interpreter_whose_path_has_spaces(
        self, spaced_interpreter, tmp_path
    ):
        correctness_test, _ = _python_api_for(spaced_interpreter)

        result = correctness_test(PASSING_CANDIDATE, str(tmp_path), TIMEOUT_SECONDS)

        assert result.passed is True, result.logs
        assert "OK" in result.logs

    def test_spaces_in_both_the_interpreter_and_the_working_directory(
        self, spaced_interpreter, spaced_dir
    ):
        correctness_test, _ = _python_api_for(spaced_interpreter)

        result = correctness_test(PASSING_CANDIDATE, str(spaced_dir), TIMEOUT_SECONDS)

        assert result.passed is True, result.logs
        assert "OK" in result.logs

    def test_the_interpreter_alias_really_does_contain_a_space(self, spaced_interpreter):
        """Guards against the fixture quietly losing the property under test."""
        assert " " in spaced_interpreter


class TestRunWithTimeoutArgumentHandling:
    def test_an_argument_list_is_not_re_split_on_whitespace(self, spaced_interpreter, spaced_dir):
        output = core.run_with_timeout(
            [spaced_interpreter, "-c", "print('argv-ok')"], TIMEOUT_SECONDS, str(spaced_dir)
        )

        assert "argv-ok" in output

    def test_an_argument_containing_spaces_arrives_as_one_argument(self, spaced_dir):
        """The general property: argv elements are passed through verbatim."""
        output = core.run_with_timeout(
            [sys.executable, "-c", "import sys; print(len(sys.argv), sys.argv[1])", "one two three"],
            TIMEOUT_SECONDS,
            str(spaced_dir),
        )

        assert "2 one two three" in output

    def test_a_command_string_is_still_accepted(self, spaced_dir):
        """Java, C++, Go and Rust still pass literal command strings."""
        output = core.run_with_timeout("echo string-form-ok", TIMEOUT_SECONDS, str(spaced_dir))

        assert "string-form-ok" in output

    def test_a_nonzero_exit_still_raises_with_the_command_in_the_message(self, spaced_dir):
        """Exit-code handling and the diagnostic are both unchanged in shape.

        The message now renders the argv rather than the caller's string, so a
        spaced path is shown quoted instead of as an ambiguous bare path.
        """
        with pytest.raises(RuntimeError) as excinfo:
            core.run_with_timeout([sys.executable, "-c", "raise SystemExit(3)"], TIMEOUT_SECONDS, str(spaced_dir))

        message = str(excinfo.value)
        assert message.startswith("Command '")
        assert "failed" in message
        assert sys.executable in message

    def test_a_string_command_is_reported_unchanged_in_the_message(self, spaced_dir):
        """The Java/C++/Go/Rust backends' diagnostics look exactly as before."""
        with pytest.raises(RuntimeError) as excinfo:
            core.run_with_timeout("false", TIMEOUT_SECONDS, str(spaced_dir))

        assert str(excinfo.value).startswith("Command 'false' failed:")

    def test_the_timeout_still_bounds_an_overrunning_command(self, spaced_dir):
        with pytest.raises(RuntimeError):
            core.run_with_timeout([sys.executable, "-c", "import time; time.sleep(30)"], 1, str(spaced_dir))

    def test_both_streams_are_still_captured(self, spaced_dir):
        output = core.run_with_timeout(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.write('out-marker\\n'); sys.stderr.write('err-marker\\n')",
            ],
            TIMEOUT_SECONDS,
            str(spaced_dir),
        )

        assert "out-marker" in output
        assert "err-marker" in output


class TestTheProfilingPathIsAlsoSpaceSafe:
    """``refine_test`` shared the defect: same ``shlex.split``, same breakage.

    The profiling pass is where PerfOrch's actual cost numbers come from, so it
    matters at least as much as the correctness pass. ``cmdbench`` takes a
    command *string*, so this path still builds one -- but it now quotes a
    correct argv rather than re-splitting an interpolated string. cmdbench is
    not installed in CI, and the property under test is the command handed to
    it, not what it measures, so it is stubbed.
    """

    @staticmethod
    def _capture_profiling_command(monkeypatch, command, temp_dir, timeout=30):
        import types

        captured = {}

        stub = types.ModuleType("cmdbench")
        stub.benchmark_command = lambda command_str, iterations_num=1: captured.setdefault(
            "cmd", command_str
        )
        monkeypatch.setitem(sys.modules, "cmdbench", stub)

        core._run_cmdbench(temp_dir, timeout, command, iterations_num=3)
        return captured["cmd"]

    def test_the_interpreter_path_stays_one_argument_through_cmdbench(
        self, monkeypatch, spaced_interpreter, spaced_dir
    ):
        import shlex

        built = self._capture_profiling_command(
            monkeypatch, [spaced_interpreter, "main.py"], str(spaced_dir)
        )

        # Recover the argv the shell would actually exec.
        bash_argv = shlex.split(built)
        assert bash_argv[:2] == ["bash", "-lc"]
        cd_part, _, run_part = bash_argv[2].partition(" && ")

        assert shlex.split(cd_part)[1] == str(spaced_dir), "the working directory was mangled"
        assert shlex.split(run_part) == [
            "timeout",
            "--signal=SIGKILL",
            "30",
            spaced_interpreter,
            "main.py",
        ]

    def test_a_literal_command_string_still_profiles(self, monkeypatch, spaced_dir):
        import shlex

        built = self._capture_profiling_command(monkeypatch, "java Main", str(spaced_dir))

        run_part = shlex.split(built)[2].partition(" && ")[2]
        assert shlex.split(run_part)[-2:] == ["java", "Main"]


class TestTheBackendNoLongerBuildsAShellString:
    """Structural guard: the class of bug, not just this instance of it."""

    def test_the_python_backend_declares_its_command_as_an_argument_list(self):
        assert isinstance(python_processor.RUN_CMD, list)
        assert isinstance(python_processor.MEMORY_CMD, list)

    def test_the_interpreter_is_a_single_unsplit_argument(self):
        # The whole point: whatever spaces sys.executable contains, it stays
        # one argv element.
        assert python_processor.RUN_CMD[0] == python_processor.PYTHON_BIN
        assert python_processor.RUN_CMD[1:] == ["main.py"]
