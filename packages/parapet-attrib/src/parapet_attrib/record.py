"""Writing the measured-cost half of a hardening record."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__

try:  # pragma: no cover - depends on whether the extra is installed
    from parapet_record import (CostMeasure, HardeningRecord, ToolResult,
                                load_record, new_provenance, save_record)
    HAVE_RECORD = True
except ImportError:  # pragma: no cover
    HAVE_RECORD = False

COMPONENT = "parapet-attrib"

# The record's dimensions, and which profile metric fills each.
DIMENSION_FOR_METRIC = {"time": "latency", "own_time": "latency", "count": "cpu"}


def cost_payload(result, before, after) -> List[Dict[str, Any]]:
    """The measured cost, in the record's own vocabulary.

    No interval is recorded. Two profiles are two samples, and a budget
    decision needs a distribution; ``parapet-record`` treats a cost with no
    interval as unable to decide, which is the correct outcome here. Feed
    repeated runs and set the interval explicitly to make the record
    decidable.
    """
    dimension = DIMENSION_FOR_METRIC.get(result.metric, "latency")
    return [{
        "dimension": dimension,
        "value": result.total_after,
        "unit": after.unit,
        "interval_low": None,
        "interval_high": None,
        "baseline": result.total_before,
        "workload": before.label or "unnamed",
        "n_samples": 1,
        "settled": False,
    }]


def write_record(path: Path, result, before, after, command: str = "") -> Path:
    """Write, or fold into, the record for one change."""
    path = Path(path)
    if path.is_dir():
        name = result.change_ref or "attribution"
        path = path / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    costs = cost_payload(result, before, after)
    attribution = {"where": result.where(),
                   "contained": result.contained,
                   "in_changed_methods": result.in_changed_methods,
                   "in_callees": result.in_callees,
                   "in_callers": result.in_callers,
                   "outside_space": result.outside_space,
                   "space_size": result.space_size,
                   "graph_size": result.graph_size,
                   "patterns": result.patterns,
                   "top_contributors": result.top_contributors[:10]}

    if not HAVE_RECORD:
        existing = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        existing.setdefault("schema_version", "1.0.0")
        existing.setdefault("record_id", result.change_ref or "attribution")
        existing.setdefault("costs", []).extend(costs)
        existing["attribution"] = attribution
        existing.setdefault("components", []).append({
            "component": COMPONENT,
            "provenance": {"tool": COMPONENT, "tool_version": __version__,
                           "command": command},
            "payload": {"before": before.summary(), "after": after.summary()}})
        existing.setdefault("warnings", []).extend(result.warnings)
        existing["warnings"].append(
            "parapet-record is not installed, so this record has no input "
            "hashes or environment profile")
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return path

    record = load_record(path) if path.exists() else HardeningRecord(
        record_id=result.change_ref or "attribution")
    record.costs.extend(CostMeasure(**item) for item in costs)
    record.attribution.update(attribution)
    record.warnings.extend(result.warnings)
    record.add(ToolResult(
        component=COMPONENT,
        provenance=new_provenance(
            COMPONENT, __version__,
            inputs={"before_profile": before.source or before.label,
                    "after_profile": after.source or after.label},
            command=command),
        payload={"before": before.summary(), "after": after.summary()}))
    record.decide()
    save_record(record, path)
    return path
