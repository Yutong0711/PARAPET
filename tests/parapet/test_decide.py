"""Functional tests for parapet.decide (no model, no JDK)."""

from __future__ import annotations

from parapet.budget import parse_budget
from parapet.decide import decide

BUDGET = parse_budget({"version": 1, "profile": "strict", "workload": "legitimate-path",
                       "caps": {"latency_overhead_pct": 5.0, "peak_memory_overhead_pct": 5.0}}, raw=b"b")


def cost(lat_hi, mem_hi):
    return {"latency": {"overhead_pct_hi": lat_hi}, "peak_memory": {"overhead_pct_hi": mem_hi}}


def test_upper_bound_exactly_at_cap_fits():
    d = decide([{"patch_id": "R1", "admissible": True, "cost": cost(5.0, 5.0)}], BUDGET, "legitimate-path")
    assert d["fitting"] == ["R1"] and d["recommended"] == "R1"


def test_upper_bound_above_either_cap_does_not_fit():
    d = decide([
        {"patch_id": "A", "admissible": True, "cost": cost(5.01, 0.0)},
        {"patch_id": "B", "admissible": True, "cost": cost(0.0, 5.01)},
    ], BUDGET, "legitimate-path")
    assert d["fitting"] == [] and d["recommended"] is None
    assert "no admissible patch fits" in d["statement"]


def test_recommend_lowest_latency_upper_bound_then_memory_then_id():
    d = decide([
        {"patch_id": "R1", "admissible": True, "cost": cost(3.0, 1.0)},
        {"patch_id": "R2", "admissible": True, "cost": cost(-20.0, 4.0)},
        {"patch_id": "G1", "admissible": True, "cost": cost(-20.0, 2.0)},
        {"patch_id": "G2", "admissible": True, "cost": cost(-20.0, 2.0)},
    ], BUDGET, "legitimate-path")
    assert d["fitting"] == ["G1", "G2", "R2", "R1"]
    assert d["recommended"] == "G1"


def test_inadmissible_or_unmeasured_patches_never_fit():
    d = decide([
        {"patch_id": "X", "admissible": False, "cost": cost(-50.0, -50.0)},
        {"patch_id": "Y", "admissible": True, "cost": None},
    ], BUDGET, "legitimate-path")
    assert d["fitting"] == []
    reasons = {r["patch_id"]: r["reasons"] for r in d["assessed"]}
    assert any("not admissible" in r for r in reasons["X"])
    assert any("no valid cost estimate" in r for r in reasons["Y"])


def test_workload_mismatch_blocks_fit():
    d = decide([{"patch_id": "R1", "admissible": True, "cost": cost(0.0, 0.0)}], BUDGET, "other-workload")
    assert d["fitting"] == []
