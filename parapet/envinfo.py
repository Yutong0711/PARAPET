# SPDX-License-Identifier: Apache-2.0
"""Environment capture for hardening records."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def _run(cmd) -> str:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (p.stdout + p.stderr).strip()
    except Exception as e:  # pragma: no cover
        return f"unavailable: {e.__class__.__name__}"


def _os_release() -> str:
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    except OSError:
        pass
    return platform.platform()


def _cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor()


def _ram_gib() -> float | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / (1024 * 1024), 2)
    except OSError:
        pass
    return None


def capture() -> dict:
    import numpy

    gpu = _run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    try:
        import openai
        openai_v = openai.__version__
    except Exception:  # pragma: no cover
        openai_v = None
    java = _run(["java", "-version"]).splitlines()
    return {
        "os": _os_release(),
        "kernel": platform.release(),
        "wsl": "microsoft" in platform.release().lower(),
        "cpu": _cpu_model(),
        "logical_cpus": os.cpu_count(),
        "ram_gib": _ram_gib(),
        "gpu": gpu,
        "jdk": java[0] if java else None,
        "jdk_full": java,
        "javac": _run(["javac", "-version"]),
        "python": sys.version.split()[0],
        "python_packages": {"numpy": numpy.__version__, "openai": openai_v},
        "loadavg": os.getloadavg(),
        "cwd_is_linux_fs": not str(Path.cwd()).startswith("/mnt/"),
    }
