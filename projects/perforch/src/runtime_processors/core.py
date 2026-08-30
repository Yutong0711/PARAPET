import os
import shlex
import shutil
import signal
import subprocess
import sys
import json
from collections.abc import Sequence
from dataclasses import dataclass
import numpy as np

BASE_RUN_TIMES = 1000
BENCHMARK_RUN_TIMES = {
    "humanevalpack": 1000,
    "effibenchx": 1000,
}
CORRECTNESS_TIMEOUT = 180
PROFILE_TIMEOUT = 300
PROFILE_CMDBENCH_ITERATIONS = 3


@dataclass(slots=True)
class TestProcessorResult:
    passed: bool
    logs: str = ""
    max_memory: float | None = None
    average_memory: float | None = None
    execution_time_all: float | None = None
    cpus_utilized: float | None = None



def setup_environment(language: str, tmp_dir: str) -> None:
    runtime_files = {
        "go": ("tool/runtime_env/go", ("go.mod", "go.sum")),
        "rust": ("tool/runtime_env/rust", ("Cargo.toml", "Cargo.lock")),
    }
    if language not in runtime_files:
        return
    base_dir, filenames = runtime_files[language]
    for name in filenames:
        shutil.copy2(os.path.join(base_dir, name), os.path.join(tmp_dir, name))


def _compile_once(compile_fn, temp_dir: str, timeout: int):
    if compile_fn is None:
        return True, ""
    if isinstance(compile_fn, str):
        try:
            return True, run_with_timeout(compile_fn, timeout, temp_dir)
        except Exception as e:
            return False, str(e)
    if callable(compile_fn):
        return compile_fn(temp_dir, timeout)
    raise TypeError(f"Unsupported compile_fn type: {type(compile_fn).__name__}")


def _as_argv(command) -> list[str]:
    """Normalise a command to an argv list without shell parsing.

    A list or tuple is already argv and is passed through element by element:
    an element may contain spaces (an interpreter path such as
    ``/mnt/d/Funding/2026 PESOSE/.../python3``) and still be one argument.
    Only a plain string is split, with ``shlex``, for the backends that
    configure a fixed literal command ("java Main", "cargo build").

    Interpolating a path into a command string and re-splitting it is what
    broke the Python backend on any checkout whose path contains a space, so
    callers that build a command from a path must pass a list.
    """
    if isinstance(command, (list, tuple)):
        argv = [str(part) for part in command]
        if not argv:
            raise ValueError("command must not be empty")
        return argv
    if isinstance(command, str):
        argv = shlex.split(command)
        if not argv:
            raise ValueError("command must not be empty")
        return argv
    raise TypeError(f"Unsupported command type: {type(command).__name__}")


def run_with_timeout(command, timeout, cwd=None, env=None):
    """
    Run a command with a specified timeout using the Linux `timeout` command.

    :param command: Command to run: an argv list (preferred, and required when
        any argument contains spaces) or a literal command string.
    :param timeout: Timeout in seconds.
    :param cwd: Directory to run the command in.
    :param env: Environment variables dictionary.
    :return: A tuple of (stdout, stderr).
    :raises: RuntimeError if the command fails.
    """
    # Normalise to argv. No shell is involved, so an argument may contain
    # spaces; cwd is handed to Popen directly for the same reason.
    command_list = _as_argv(command)
    # Enable timeout automatically when timeout is a positive number.
    if timeout is not None and timeout > 0:
        full_command = ["timeout", "--signal=SIGKILL", str(timeout)] + command_list
    else:
        full_command = command_list
    proc = None
    try:
        proc = subprocess.Popen(
            full_command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            preexec_fn=os.setsid,
        )
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            stderr_s = (stderr or "").strip()
            stdout_s = (stdout or "").strip()
            details = stderr_s or stdout_s or f"exit code={proc.returncode}"
            raise RuntimeError(f"Command '{shlex.join(command_list)}' failed: {details}")
        return (stdout or "") + (stderr or "")
    except KeyboardInterrupt:
        if proc is not None and proc.pid is not None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
        raise


def _run_cmdbench(temp_dir: str, timeout: int, command, iterations_num: int = 1):
    import cmdbench

    if command is None or not str(command).strip():
        raise ValueError("command must not be empty")

    # Same rule as run_with_timeout: an argv list is never re-split. cmdbench
    # takes a command string, so the tokens are re-quoted with shlex.quote
    # below -- quoting a correct argv, rather than hoping a built string
    # survives a round trip through shlex.split.
    tokens = _as_argv(command)
    first = tokens[0]
    if first.startswith("./") or first.startswith("target/"):
        abs_first = os.path.join(temp_dir, first)
        if not os.path.exists(abs_first):
            raise FileNotFoundError(abs_first)
        tokens[0] = abs_first

    if timeout and timeout > 0:
        tokens = ["timeout", "--signal=SIGKILL", str(timeout)] + tokens

    command_str = " ".join(shlex.quote(part) for part in tokens)
    if temp_dir:
        command_str = f"cd {shlex.quote(temp_dir)} && {command_str}"
    command_str = f"bash -lc {shlex.quote(command_str)}"
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    if orig_stdout is None or getattr(orig_stdout, "encoding", None) is None:
        sys.stdout = sys.__stdout__
    if orig_stderr is None or getattr(orig_stderr, "encoding", None) is None:
        sys.stderr = sys.__stderr__
    try:
        if sys.stdout and getattr(sys.stdout, "encoding", None) is None and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and getattr(sys.stderr, "encoding", None) is None and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        return cmdbench.benchmark_command(command_str, iterations_num=iterations_num)
    finally:
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


def _extract_profile_metrics(averages):
    try:
        execution_time = averages["process"]["execution_time"]
    except Exception:
        raise ValueError("cmdbench result missing process execution_time")
    execution_time_ms = float(execution_time) * 1000.0

    cpus_utilized = None
    try:
        cpu_total_time = averages["cpu"]["total_time"]
        if execution_time and execution_time > 0:
            cpus_utilized = float(cpu_total_time) / float(execution_time)
    except Exception:
        cpus_utilized = None

    max_data_stk_sum = None
    try:
        max_data_stk_sum = float(averages["memory"]["max"])
        if (not np.isfinite(max_data_stk_sum)) or max_data_stk_sum <= 0:
            max_data_stk_sum = None
    except Exception:
        max_data_stk_sum = None

    average_data_stk_sum = None
    finite_mem = None
    try:
        time_series = averages["time_series"]
        mem_series = time_series["memory_bytes"]
        if mem_series is not None:
            mem_array = np.asarray(mem_series, dtype=float)
            finite_mem = mem_array[np.isfinite(mem_array)]
            if finite_mem.size > 0:
                average_data_stk_sum = float(np.mean(finite_mem))
    except Exception:
        average_data_stk_sum = None

    if max_data_stk_sum is None and finite_mem is not None and finite_mem.size > 0:
        max_data_stk_sum = float(np.max(finite_mem))

    return execution_time_ms, cpus_utilized, max_data_stk_sum, average_data_stk_sum


def _safe_nested_get(mapping, *keys):
    curr = mapping
    for key in keys:
        try:
            curr = curr[key]
        except Exception:
            return None
    return curr


def _sanitize_for_json(value):
    if isinstance(value, dict):
        return {k: _sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_json(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_sanitize_for_json(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return _sanitize_for_json(value.item())
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    return value


def _format_cmdbench_logs(
    stats,
    averages,
    execution_time_ms: float | None,
    cpus_utilized: float | None,
    max_memory: float | None,
    average_memory: float | None,
) -> str:
    payload = {
        "cmdbench": {
            "iterations": len(getattr(stats, "iterations", []) or []),
            "process_execution_time_s": _safe_nested_get(averages, "process", "execution_time"),
            "process_exit_code": _safe_nested_get(averages, "process", "exit_code"),
            "cpu_total_time_s": _safe_nested_get(averages, "cpu", "total_time"),
            "memory_max_bytes": _safe_nested_get(averages, "memory", "max"),
        },
        "derived_metrics": {
            "execution_time_ms": execution_time_ms,
            "cpus_utilized": cpus_utilized,
            "max_memory_bytes": max_memory,
            "average_memory_bytes": average_memory,
        },
    }
    return json.dumps(_sanitize_for_json(payload), ensure_ascii=False, sort_keys=True)

def correctness_test(
    complete_code: str,
    temp_dir: str,
    timeout: int,
    *,
    source_relpath: str,
    compile_fn,
    run_cmd: str | Sequence[str],
    post_write_fn=None,
) -> TestProcessorResult:
    file_path = os.path.join(temp_dir, source_relpath)
    parent = os.path.dirname(file_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(file_path, "w") as file:
        file.write(complete_code)

    try:
        if post_write_fn is not None:
            post_write_fn(file_path)
        compile_success, compile_output = _compile_once(compile_fn, temp_dir, timeout)
        if not compile_success:
            msg = f"Compilation failed: {compile_output}"
            return TestProcessorResult(
                passed=False,
                logs=msg,
            )
        command_output = run_with_timeout(run_cmd, timeout, temp_dir)
        return TestProcessorResult(
            passed=True,
            logs=command_output,
        )
    except Exception as e:
        err = str(e)
        return TestProcessorResult(
            passed=False,
            logs=err,
        )


def refine_test(
    base_run_times: int,
    temp_dir: str,
    timeout: int,
    *,
    source_relpath: str,
    wrap_fn,
    compile_fn,
    memory_cmd: str | Sequence[str],
) -> TestProcessorResult:
    try:
        source_path = os.path.join(temp_dir, source_relpath)
        if wrap_fn is None:
            err = "wrap_fn is required for refine_test"
            print(err)
            return TestProcessorResult(
                passed=False,
                logs=err,
            )

        with open(source_path, "r") as file:
            original = file.read()

        wrapped = wrap_fn(original, base_run_times)
        with open(source_path, "w") as file:
            file.write(wrapped)

        compile_success, compile_output = _compile_once(compile_fn, temp_dir, timeout)
        if not compile_success:
            msg = f"Compilation failed: {compile_output}"
            return TestProcessorResult(
                passed=False,
                logs=msg,
            )

        stats = _run_cmdbench(
            temp_dir,
            timeout,
            memory_cmd,
            iterations_num=PROFILE_CMDBENCH_ITERATIONS,
        )
        averages = stats.get_averages()

        execution_time, cpus_utilized, max_memory, average_memory = _extract_profile_metrics(averages)

        run_logs = _format_cmdbench_logs(
            stats,
            averages,
            execution_time_ms=execution_time,
            cpus_utilized=cpus_utilized,
            max_memory=max_memory,
            average_memory=average_memory,
        )

        return TestProcessorResult(
            passed=True,
            logs=run_logs,
            max_memory=max_memory,
            average_memory=average_memory,
            execution_time_all=execution_time,
            cpus_utilized=cpus_utilized,
        )
    except Exception as e:
        print(e)
        err = str(e)
        return TestProcessorResult(
            passed=False,
            logs=err,
        )


def build_processor_api(
    *,
    source_relpath: str,
    wrap_fn,
    compile_fn,
    run_cmd: str | Sequence[str],
    memory_cmd: str | Sequence[str],
    post_write_fn=None,
):
    def _correctness_test(complete_code, temp_dir, timeout):
        return correctness_test(
            complete_code,
            temp_dir,
            timeout,
            source_relpath=source_relpath,
            compile_fn=compile_fn,
            run_cmd=run_cmd,
            post_write_fn=post_write_fn,
        )

    def _refine_test(base_run_times, temp_dir, timeout):
        return refine_test(
            base_run_times,
            temp_dir,
            timeout,
            source_relpath=source_relpath,
            wrap_fn=wrap_fn,
            compile_fn=compile_fn,
            memory_cmd=memory_cmd,
        )

    return _correctness_test, _refine_test
