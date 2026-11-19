# SPDX-License-Identifier: Apache-2.0
"""Decide stage: which admissible patches fit a pre-declared budget.

Rule (parapet/settings/decision_rule.yaml): a patch fits only if it is
admissible, has a valid cost estimate, and the UPPER end of the 95% interval
of both its latency overhead and its peak-memory overhead is at or below the
budget's caps. Among patches that fit, recommend the lowest latency upper
bound (ties: lower memory upper bound, then patch id).
"""

from __future__ import annotations

from parapet.budget import Budget


def assess(patch_id: str, admissible: bool, cost: dict | None, budget: Budget, workload: str) -> dict:
    reasons = []
    if budget.workload != workload:
        reasons.append(f"budget workload {budget.workload!r} != measured workload {workload!r}")
    if not admissible:
        reasons.append("not admissible (below L4)")
    if cost is None:
        reasons.append("no valid cost estimate")
    lat_hi = mem_hi = None
    if cost is not None:
        lat_hi = cost["latency"]["overhead_pct_hi"]
        mem_hi = cost["peak_memory"]["overhead_pct_hi"]
        if lat_hi > budget.latency_overhead_pct:
            reasons.append(f"latency overhead upper bound {lat_hi:.2f}% > cap {budget.latency_overhead_pct}%")
        if mem_hi > budget.peak_memory_overhead_pct:
            reasons.append(f"peak-memory overhead upper bound {mem_hi:.2f}% > cap {budget.peak_memory_overhead_pct}%")
    return {
        "patch_id": patch_id,
        "fits": not reasons,
        "latency_overhead_pct_hi": lat_hi,
        "peak_memory_overhead_pct_hi": mem_hi,
        "reasons": reasons,
    }


def decide(patches: list, budget: Budget, workload: str) -> dict:
    """patches: dicts with keys patch_id, admissible, cost (vs-baseline comparison or None)."""
    rows = [assess(p["patch_id"], p["admissible"], p.get("cost"), budget, workload) for p in patches]
    fitting = [r for r in rows if r["fits"]]
    fitting.sort(key=lambda r: (r["latency_overhead_pct_hi"], r["peak_memory_overhead_pct_hi"], r["patch_id"]))
    rec = fitting[0]["patch_id"] if fitting else None
    return {
        "profile": budget.profile,
        "budget_path": budget.path,
        "budget_sha256": budget.sha256,
        "caps": budget.caps(),
        "workload": workload,
        "assessed": rows,
        "fitting": [r["patch_id"] for r in fitting],
        "recommended": rec,
        "statement": (f"recommend {rec}" if rec else
                      f"no admissible patch fits the {budget.profile} budget; recommend none"),
    }
