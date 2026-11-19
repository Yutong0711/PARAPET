# SPDX-License-Identifier: Apache-2.0
"""Reuse of the vendored PerfOrch snapshot, by import only.

Nothing under ``projects/`` is modified. PerfOrch's source tree is put on
``sys.path`` the same way ``tests/conftest.py`` does, and models are
registered by adding entries to ``config.api_config.API_CONFIG`` at runtime.

Reused pieces:

* ``llm_generator.generate_text`` -- every model call goes through it;
* ``runtime_processors.core.run_with_timeout`` -- every javac/java run of a
  validation check goes through it (argv list, ``timeout --signal=SIGKILL``).

Workload measurement uses a thin runner (parapet.measure) instead of PerfOrch's
``refine_test``; see that module for why.
"""

from __future__ import annotations

import sys

from parapet.paths import PERFORCH_SRC


def ensure_on_path() -> None:
    p = str(PERFORCH_SRC)
    if p not in sys.path:
        sys.path.insert(0, p)


def runtime_core():
    ensure_on_path()
    from runtime_processors import core  # noqa: WPS433 (vendored import)

    return core


def llm_generator():
    ensure_on_path()
    import llm_generator  # noqa: WPS433

    return llm_generator


def api_config() -> dict:
    ensure_on_path()
    from config.api_config import API_CONFIG  # noqa: WPS433

    return API_CONFIG


def register_model(product_name: str, *, model: str, base_url: str, api_key: str, rpm=None) -> None:
    """Add (or replace) one entry in PerfOrch's API_CONFIG, in memory only."""
    entry = {"type": "openai-sdk", "model": model, "api_key": api_key, "base_url": base_url}
    if rpm:
        entry["RPM"] = rpm
    api_config()[product_name] = entry
