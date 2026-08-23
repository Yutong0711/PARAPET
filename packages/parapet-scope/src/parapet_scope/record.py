"""Writing the review-cost half of a hardening record."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from . import __version__

try:  # pragma: no cover - depends on whether the extra is installed
    from parapet_record import (HardeningRecord, ReviewCost, ToolResult,
                                load_record, new_provenance, save_record)
    HAVE_RECORD = True
except ImportError:  # pragma: no cover
    HAVE_RECORD = False

COMPONENT = "parapet-scope"


def review_cost_payload(verdict, diff) -> Dict[str, Any]:
    return {"n_production_files": verdict.n_production_files,
            "n_test_files": verdict.n_test_files,
            "scope": verdict.scope,
            "design_pattern": verdict.design_pattern,
            "cochange_patterns": list(verdict.cochange_patterns),
            "added_dependencies": verdict.added_dependencies,
            "removed_dependencies": verdict.removed_dependencies,
            "added_files": list(verdict.added_files),
            "removed_files": list(verdict.removed_files),
            "notes": "; ".join(verdict.notes)}


def write_record(path: Path, verdict, diff, revision,
                 command: str = "") -> Path:
    """Write, or update in place, the record for one revision.

    When ``path`` already holds a record, the review cost is folded into
    it rather than replacing it: ``parapet-triage`` may have written the
    exposure there first, and the point of the schema is that the parts
    compose.
    """
    path = Path(path)
    if path.is_dir():
        path = path / f"{revision.short}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = review_cost_payload(verdict, diff)

    if not HAVE_RECORD:
        existing = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = {}
        existing.setdefault("schema_version", "1.0.0")
        existing.setdefault("record_id", revision.short)
        existing["change_ref"] = revision.commit
        existing["review_cost"] = payload
        existing.setdefault("components", []).append({
            "component": COMPONENT,
            "provenance": {"tool": COMPONENT, "tool_version": __version__,
                           "command": command},
            "payload": {"diff_dsm": diff.to_dict()}})
        existing.setdefault("warnings", []).append(
            "parapet-record is not installed, so this record has no input "
            "hashes or environment profile")
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return path

    record = load_record(path) if path.exists() else HardeningRecord(
        record_id=revision.short)
    record.change_ref = revision.commit
    record.review_cost = ReviewCost(**payload)
    record.add(ToolResult(
        component=COMPONENT,
        provenance=new_provenance(
            COMPONENT, __version__,
            inputs={"commit": revision.commit, "base": revision.base},
            repo=revision.repo, command=command),
        payload={"diff_dsm": diff.to_dict()}))
    record.decide()
    save_record(record, path)
    return path
