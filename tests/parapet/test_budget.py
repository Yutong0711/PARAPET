"""Functional tests for parapet.budget (no model, no JDK)."""

from __future__ import annotations

import pytest
import yaml

from parapet.budget import BudgetError, load_budget, parse_budget
from parapet.paths import BUDGETS_DIR

VALID = {
    "version": 1,
    "profile": "p",
    "workload": "legitimate-path",
    "caps": {"latency_overhead_pct": 5, "peak_memory_overhead_pct": 7.5},
}


def test_committed_profiles_load():
    strict = load_budget(BUDGETS_DIR / "strict.parapet.budget.yaml")
    lenient = load_budget(BUDGETS_DIR / "lenient.parapet.budget.yaml")
    assert (strict.profile, strict.latency_overhead_pct, strict.peak_memory_overhead_pct) == ("strict", 5.0, 5.0)
    assert (lenient.profile, lenient.latency_overhead_pct, lenient.peak_memory_overhead_pct) == ("lenient", 25.0, 25.0)
    assert strict.workload == lenient.workload == "legitimate-path"
    assert len(strict.sha256) == 64 and strict.sha256 != lenient.sha256


def test_valid_budget_parses_and_coerces_numbers():
    b = parse_budget(VALID, raw=b"x")
    assert b.latency_overhead_pct == 5.0 and isinstance(b.latency_overhead_pct, float)
    assert b.caps() == {"latency_overhead_pct": 5.0, "peak_memory_overhead_pct": 7.5}


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d.pop("caps"), "missing budget keys"),
        (lambda d: d.update(version=2), "unsupported budget version"),
        (lambda d: d.update(version=True), "unsupported budget version"),
        (lambda d: d.update(profile=""), "profile"),
        (lambda d: d.update(workload="  "), "workload"),
        (lambda d: d.update(extra=1), "unknown budget keys"),
        (lambda d: d["caps"].update(latency_overhead_pct=-1), ">= 0"),
        (lambda d: d["caps"].update(latency_overhead_pct="5"), "must be a number"),
        (lambda d: d["caps"].update(peak_memory_overhead_pct=float("inf")), "finite"),
        (lambda d: d["caps"].pop("peak_memory_overhead_pct"), "missing caps"),
        (lambda d: d["caps"].update(cpu_pct=3), "unknown caps"),
    ],
)
def test_invalid_budgets_are_rejected(mutate, message):
    data = yaml.safe_load(yaml.safe_dump(VALID))
    mutate(data)
    with pytest.raises(BudgetError, match=message):
        parse_budget(data)


def test_load_budget_reports_missing_file(tmp_path):
    with pytest.raises(BudgetError, match="not found"):
        load_budget(tmp_path / "nope.yaml")


def test_hash_tracks_file_bytes(tmp_path):
    p = tmp_path / "parapet.budget.yaml"
    p.write_text(yaml.safe_dump(VALID))
    h1 = load_budget(p).sha256
    p.write_text(yaml.safe_dump(VALID) + "# changed\n")
    assert load_budget(p).sha256 != h1
