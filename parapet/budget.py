# SPDX-License-Identifier: Apache-2.0
"""Service budgets: the cost a maintainer allows security hardening to add.

A budget lives in a ``parapet.budget.yaml`` file, declared before any
measurement. Schema (version 1)::

    version: 1
    profile: strict                  # a name for this budget
    workload: legitimate-path        # the named workload the caps apply to
    caps:
      latency_overhead_pct: 5.0      # max added latency, percent of baseline
      peak_memory_overhead_pct: 5.0  # max added peak memory, percent of baseline
    description: optional free text

Unknown keys are rejected rather than ignored, so a typo cannot silently
loosen a budget. The SHA-256 of the file bytes is carried into every record.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from parapet.hashing import sha256_bytes

SUPPORTED_VERSIONS = (1,)
TOP_LEVEL_KEYS = {"version", "profile", "workload", "caps", "description"}
CAP_KEYS = {"latency_overhead_pct", "peak_memory_overhead_pct"}


class BudgetError(ValueError):
    """The budget file is missing, malformed, or violates the schema."""


@dataclass(frozen=True)
class Budget:
    version: int
    profile: str
    workload: str
    latency_overhead_pct: float
    peak_memory_overhead_pct: float
    description: str
    path: str
    sha256: str

    def caps(self) -> dict:
        return {
            "latency_overhead_pct": self.latency_overhead_pct,
            "peak_memory_overhead_pct": self.peak_memory_overhead_pct,
        }

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "profile": self.profile,
            "workload": self.workload,
            "caps": self.caps(),
            "description": self.description,
            "path": self.path,
            "sha256": self.sha256,
        }


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BudgetError(f"caps.{name} must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise BudgetError(f"caps.{name} must be finite, got {value!r}")
    if value < 0:
        raise BudgetError(f"caps.{name} must be >= 0, got {value!r}")
    return value


def parse_budget(data, *, path: str = "<memory>", raw: bytes = b"") -> Budget:
    if not isinstance(data, dict):
        raise BudgetError("budget must be a YAML mapping")
    unknown = set(data) - TOP_LEVEL_KEYS
    if unknown:
        raise BudgetError(f"unknown budget keys: {sorted(unknown)}")
    missing = {"version", "profile", "workload", "caps"} - set(data)
    if missing:
        raise BudgetError(f"missing budget keys: {sorted(missing)}")
    version = data["version"]
    if isinstance(version, bool) or version not in SUPPORTED_VERSIONS:
        raise BudgetError(f"unsupported budget version {version!r}; supported: {SUPPORTED_VERSIONS}")
    profile = data["profile"]
    if not isinstance(profile, str) or not profile.strip():
        raise BudgetError("profile must be a non-empty string")
    workload = data["workload"]
    if not isinstance(workload, str) or not workload.strip():
        raise BudgetError("workload must be a non-empty string")
    caps = data["caps"]
    if not isinstance(caps, dict):
        raise BudgetError("caps must be a mapping")
    unknown_caps = set(caps) - CAP_KEYS
    if unknown_caps:
        raise BudgetError(f"unknown caps: {sorted(unknown_caps)}")
    missing_caps = CAP_KEYS - set(caps)
    if missing_caps:
        raise BudgetError(f"missing caps: {sorted(missing_caps)}")
    description = data.get("description", "") or ""
    if not isinstance(description, str):
        raise BudgetError("description must be a string")
    return Budget(
        version=int(version),
        profile=profile.strip(),
        workload=workload.strip(),
        latency_overhead_pct=_number(caps["latency_overhead_pct"], "latency_overhead_pct"),
        peak_memory_overhead_pct=_number(caps["peak_memory_overhead_pct"], "peak_memory_overhead_pct"),
        description=description.strip(),
        path=path,
        sha256=sha256_bytes(raw),
    )


def load_budget(path) -> Budget:
    p = Path(path)
    if not p.is_file():
        raise BudgetError(f"budget file not found: {p}")
    raw = p.read_bytes()
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise BudgetError(f"budget file is not valid YAML: {e}") from e
    return parse_budget(data, path=str(p), raw=raw)
