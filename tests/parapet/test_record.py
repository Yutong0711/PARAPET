"""Functional tests for parapet.record (no model, no JDK)."""

from __future__ import annotations

import json

from parapet.budget import parse_budget
from parapet.case import load_case
from parapet.decide import decide
from parapet.record import REQUIRED_FIELDS, build_record, render_markdown, unified_diff, write_record


def _validation(level="L4"):
    checks = {n: {"command": f"java harness.{n}", "passed": True, "evaluated": True, "summary": "ok",
                  "result": {}} for n in ("reproducer", "heldout1", "heldout2", "functional", "probes")}
    return {"source_sha256": "ab" * 32, "compile": {"command": "javac x", "ok": True}, "checks": checks,
            "claim_level": level, "admissible": level == "L4"}


def _cost(hi):
    c = {"overhead_pct": hi - 1, "overhead_pct_lo": hi - 2, "overhead_pct_hi": hi,
         "indistinguishable_from_noise": False}
    return {"latency": dict(c), "peak_memory": dict(c)}


def test_record_has_every_required_field_and_is_json(tmp_path):
    case = load_case("C2")
    budget = parse_budget({"version": 1, "profile": "strict", "workload": "legitimate-path",
                           "caps": {"latency_overhead_pct": 5, "peak_memory_overhead_pct": 5}}, raw=b"z")
    d = decide([{"patch_id": "R1", "admissible": True, "cost": _cost(3.0)}], budget, "legitimate-path")
    original = case.read_target()
    patched = case.references["R1"].path.read_text()
    rec = build_record(
        case=case, patch={"id": "R1", "kind": "reference fix (hand-written)", "source_path": "x",
                          "mechanism": {"route": "narrowed behavior", "description": "d"}},
        validation=_validation(), probes_cmp={"evaluated": True, "now_rejected": [{"probe": "p", "exception": "E"}],
                                              "different_result": []},
        cost=_cost(3.0), cost_vs_ref=None, raw_samples={"path": "measurement/raw_samples.jsonl", "sha256": "cd" * 32},
        noise_floor={"latency_pct": 1.0, "peak_memory_pct": 0.5}, decisions=[d],
        generator={"name": "hand-written reference"}, prompt=None, environment={"os": "test"},
        reproduce="python -m parapet run --case C2 --budget b --no-generator",
        repo={"commit": "deadbeef", "branch": "b"}, original_source=original, patched_source=patched)
    for f in REQUIRED_FIELDS:
        assert f in rec, f
    assert rec["weakness"]["cwe"] == "CWE-611"
    assert "+            factory.setFeature(\"http://apache.org/xml/features/disallow-doctype-decl\", true);" in rec["diff"]
    assert rec["budgets"][0]["fits"] and rec["budgets"][0]["this_patch_recommended"]
    assert rec["budgets"][0]["claim_level"] == "L5"
    assert rec["budgets"][0]["sha256"] == budget.sha256
    jp, mp = write_record(rec, tmp_path, "R1")
    assert json.loads(jp.read_text())["patch"]["id"] == "R1"
    md = mp.read_text()
    for heading in ("## Checks", "## Inputs the original accepted", "## Cost on the workload",
                    "## Budget decisions", "## Diff", "## Reproduce"):
        assert heading in md
    assert "`p`" in md and "hand-written reference" in md


def test_unchanged_source_gives_an_empty_diff():
    assert unified_diff("a\nb\n", "a\nb\n", "X.java") == ""


def test_markdown_marks_costs_inside_the_noise_floor():
    rec = {
        "case": {"id": "C1", "title": "t"}, "weakness": {"cwe": "CWE-502", "name": "n"},
        "patch": {"id": "R1", "kind": "k", "source_sha256": "s"}, "mechanism": {"route": "r", "description": "d"},
        "claim_level": "L4", "admissible": True, "generator": {"name": "hand-written reference"},
        "prompt": None, "repo": {"commit": "c", "branch": "b"}, "checks": [],
        "inputs_now_rejected": {"evaluated": True, "now_rejected": [], "different_result": []},
        "cost": {"vs_baseline": {"latency": {"overhead_pct": 0.1, "overhead_pct_lo": -1, "overhead_pct_hi": 1,
                                             "indistinguishable_from_noise": True},
                                 "peak_memory": None}, "vs_matched_reference": None,
                 "noise_floor_pct": None, "raw_samples": None},
        "budgets": [], "diff": "", "environment": {}, "reproduce": "x",
    }
    assert "indistinguishable from the A/A noise floor" in render_markdown(rec)
