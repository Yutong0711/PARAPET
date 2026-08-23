"""Provenance: what produced a record, from what, where.

Section 5 of the PESOSE project description treats the record as
security-critical, because bending it moves a change through review
without touching the code. Three defences live here: every input is
hashed, the environment is recorded, and the command line is kept. None of
them stops a determined attacker on its own; together they make a changed
input visible to anyone who re-runs.
"""

from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional, Union

from .schema import Provenance

CHUNK = 1 << 20


def content_digest(data: Union[str, bytes]) -> str:
    """``sha256:<hex>`` over bytes or UTF-8 text."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def file_digest(path: Union[str, Path]) -> str:
    """``sha256:<hex>`` over a file, streamed."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _git(args, cwd=None) -> Optional[str]:
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                                text=True, check=False, timeout=10)
        return result.stdout.strip() or None if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def environment_profile(repo: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """The machine, interpreter and toolchain a measurement was taken on.

    A cost number is only meaningful beside the environment that produced
    it. The Linux kernel's own mitigation measurements land differently
    across configurations, which is exactly why this is recorded rather
    than assumed.
    """
    profile = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "unknown",
        "cpu_count": str(os.cpu_count() or 0),
    }
    java = _java_version()
    if java:
        profile["java"] = java
    if repo is not None:
        commit = _git(["rev-parse", "HEAD"], cwd=str(repo))
        if commit:
            profile["repo_commit"] = commit
        dirty = _git(["status", "--porcelain"], cwd=str(repo))
        profile["repo_dirty"] = "yes" if dirty else "no"
    return profile


def _java_version() -> Optional[str]:
    try:
        result = subprocess.run(["java", "-version"], capture_output=True,
                                text=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stderr or result.stdout or "").splitlines()
    return output[0].strip() if output else None


def new_provenance(tool: str, tool_version: str,
                   inputs: Optional[Dict[str, Union[str, Path]]] = None,
                   repo: Optional[Union[str, Path]] = None,
                   command: Optional[str] = None) -> Provenance:
    """Build a provenance block, hashing every input that is a real file.

    An input that is not a path is hashed as content, so a pattern set
    passed in memory is covered the same way a file on disk is.
    """
    hashed: Dict[str, str] = {}
    for name, value in (inputs or {}).items():
        try:
            path = Path(str(value))
            hashed[name] = file_digest(path) if path.is_file() else content_digest(str(value))
        except (OSError, ValueError):
            hashed[name] = content_digest(str(value))
    return Provenance(
        tool=tool,
        tool_version=tool_version,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        inputs=hashed,
        environment=environment_profile(repo),
        command=command if command is not None else " ".join(sys.argv))
