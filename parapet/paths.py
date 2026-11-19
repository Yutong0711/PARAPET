# SPDX-License-Identifier: Apache-2.0
"""Repository locations used by the PARAPET package."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
CASES_DIR = PACKAGE_DIR / "cases"
BUDGETS_DIR = PACKAGE_DIR / "budgets"
SETTINGS_DIR = PACKAGE_DIR / "settings"
PROMPTS_DIR = PACKAGE_DIR / "prompts"
PERFORCH_SRC = REPO_ROOT / "projects" / "perforch" / "src"


def default_workdir() -> Path:
    """Compile-and-measure scratch area. Must be on a Linux filesystem.

    Timing on a Windows drive mounted into WSL (/mnt/c, /mnt/d, ...) is
    distorted by 9P file I/O, so the default lives under $HOME.
    """
    env = os.environ.get("PARAPET_WORKDIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "parapet-work" / "runs"


def is_windows_mount(path: Path) -> bool:
    parts = Path(path).resolve().parts
    return len(parts) >= 3 and parts[1] == "mnt" and len(parts[2]) == 1
