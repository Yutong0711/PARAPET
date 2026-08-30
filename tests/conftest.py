"""Shared fixtures and import-path setup for the PARAPET test suite.

The vendored snapshots under ``projects/`` are not installable packages: they
are source trees that upstream expects to be run with their own ``src/``
directory on ``sys.path`` (PerfOrch uses absolute imports such as
``from llm_generator import generate_text``; CoQuIR's ``evaluate_coquir.sh``
does ``export PYTHONPATH=$ROOT_DIR/src``).

Rather than repackaging vendored code -- which would damage provenance -- the
tests reproduce that expectation here, explicitly and in one place.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS = REPO_ROOT / "projects"

# Vendored source trees that the tests import from, in the layout upstream uses.
_VENDORED_SRC_ON_PATH = (
    PROJECTS / "perforch" / "src",
    PROJECTS / "more-than-just-functional" / "src",
)

for _path in _VENDORED_SRC_ON_PATH:
    _resolved = str(_path)
    if _resolved not in sys.path:
        sys.path.insert(0, _resolved)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def projects_dir() -> Path:
    """Absolute path to the vendored ``projects/`` directory."""
    return PROJECTS
