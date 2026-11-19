# SPDX-License-Identifier: Apache-2.0
"""javac/java invocations for validation checks, via PerfOrch's runner."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from parapet.perforch_bridge import runtime_core


@dataclass
class CommandResult:
    argv: list
    ok: bool
    output: str
    duration_s: float
    timed_out: bool

    @property
    def command(self) -> str:
        return shlex.join(str(a) for a in self.argv)


def run(argv, *, timeout: int, cwd: Path | None = None) -> CommandResult:
    """Run argv through PerfOrch's ``core.run_with_timeout``.

    That function wraps the command in ``timeout --signal=SIGKILL`` and raises
    RuntimeError on a non-zero exit; its message carries stderr (or stdout).
    """
    core = runtime_core()
    t0 = time.monotonic()
    try:
        out = core.run_with_timeout([str(a) for a in argv], timeout, str(cwd) if cwd else None)
        ok = True
    except RuntimeError as e:
        out = str(e)
        ok = False
    dt = time.monotonic() - t0
    timed_out = (not ok) and dt >= timeout - 0.5
    return CommandResult(argv=[str(a) for a in argv], ok=ok, output=out, duration_s=dt, timed_out=timed_out)


def classpath(*dirs) -> str:
    return os.pathsep.join(str(d) for d in dirs if d)


def javac(sources, out_dir: Path, *, cp=(), sourcepath: Path | None = None, release: int = 17,
          timeout: int = 180) -> CommandResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    argv = ["javac", "--release", str(release), "-encoding", "UTF-8", "-d", str(out_dir)]
    if cp:
        argv += ["-cp", classpath(*cp)]
    if sourcepath is not None:
        argv += ["-sourcepath", str(sourcepath)]
    argv += [str(s) for s in sources]
    return run(argv, timeout=timeout)


def java(main: str, *, cp, args=(), sysprops=None, timeout: int = 60, flags=()) -> CommandResult:
    argv = ["java", *flags]
    for k, v in (sysprops or {}).items():
        argv.append(f"-D{k}={v}")
    argv += ["-cp", classpath(*cp), main, *[str(a) for a in args]]
    return run(argv, timeout=timeout)


def jdk_version() -> dict:
    def first_line(cmd):
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return (p.stdout + p.stderr).strip().splitlines()
        except Exception as e:  # pragma: no cover - environment probe
            return [f"unavailable: {e}"]

    return {"java": first_line(["java", "-version"]), "javac": first_line(["javac", "-version"])}
