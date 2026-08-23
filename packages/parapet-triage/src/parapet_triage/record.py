"""Writing the exposure half of a hardening record.

``parapet-triage`` fills one field of the record: the exposure. It says
what the report is about, on what evidence, and whether a reproducer was
mentioned. It does not decide anything about a fix; that is the other two
components' work.

``parapet-record`` is an optional dependency. Without it the package still
classifies, and this module writes a plain JSON document with the same
fields, so a user who installed only ``parapet-triage`` is never blocked.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import __version__

try:  # pragma: no cover - exercised by whether the extra is installed
    from parapet_record import (Exposure, HardeningRecord, ToolResult,
                                new_provenance, save_record)
    HAVE_RECORD = True
except ImportError:  # pragma: no cover
    HAVE_RECORD = False

COMPONENT = "parapet-triage"


def exposure_payload(report, verdict, kind: str = "unknown") -> Dict[str, Any]:
    """The exposure fields this component can fill, as a plain dict."""
    return {
        "identifier": report.identifier,
        "kind": kind,
        "cwe": getattr(report, "cwe", None),
        "title": report.title,
        "text": report.text[:4000],
        "reproducer": getattr(report, "reproducer", None),
        "source": report.source,
        "labels": list(verdict.patterns),
        "confidence": round(verdict.confidence, 4),
        "evidence": {
            "score": round(verdict.score, 4),
            "pattern_set": verdict.set_id,
            "backend": verdict.backend,
            "matching_sentences": [item.to_dict()
                                   for item in verdict.matching_sentences[:5]],
        },
    }


def _kind_for(set_id: str) -> str:
    if set_id.startswith("security"):
        return "security"
    if set_id.startswith("performance"):
        return "performance"
    return "unknown"


def build_records(reports: Sequence, verdicts: Sequence, triager,
                  out_dir: Path, command: str = "") -> List[Path]:
    """One record per matching report, written into ``out_dir``.

    Only matches get a record. A report that did not match has no exposure
    to record, and writing an empty record for it would put a document in
    front of a maintainer that says nothing.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    kind = _kind_for(triager.pattern_set.set_id)
    written: List[Path] = []

    for report, verdict in zip(reports, verdicts):
        if not verdict.is_match:
            continue
        payload = exposure_payload(report, verdict, kind)
        safe = "".join(char if char.isalnum() or char in "-._" else "_"
                       for char in report.identifier) or "report"
        path = out_dir / f"{safe}.json"

        if HAVE_RECORD:
            provenance = new_provenance(
                COMPONENT, __version__,
                inputs={"pattern_set": str(triager.pattern_set.path or
                                           triager.pattern_set.set_id),
                        "report_text": report.text},
                command=command)
            record = HardeningRecord(record_id=report.identifier,
                                     exposure=Exposure(**payload))
            record.add(ToolResult(component=COMPONENT, provenance=provenance,
                                  payload={"triage": triager.report()}))
            save_record(record, path)
        else:
            path.write_text(json.dumps({
                "schema_version": "1.0.0",
                "record_id": report.identifier,
                "exposure": payload,
                "components": [{"component": COMPONENT,
                                "provenance": {"tool": COMPONENT,
                                               "tool_version": __version__,
                                               "command": command},
                                "payload": {"triage": triager.report()}}],
                "warnings": ["parapet-record is not installed, so this record "
                             "has no input hashes or environment profile; "
                             "install parapet-record for a verifiable record"],
            }, indent=2), encoding="utf-8")
        written.append(path)
    return written
