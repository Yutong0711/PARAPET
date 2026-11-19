# SPDX-License-Identifier: Apache-2.0
"""Fill {{kind:arg}} placeholders in an evidence template with tables computed
from saved run directories (paths relative to evidence/mozilla-2026-11/).

Kinds: validation, claims, generation, measurement, decisions, model_induced,
power, cross (arg = case id), cpu_only (arg = run dir), endpoints (arg = run dir),
file (arg = path to include verbatim).

Usage: python build_doc.py <template.md> <output.md>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(HERE))

import tables  # noqa: E402
import cross_session  # noqa: E402

SESSIONS = [("v1 Step 2", "step2"), ("v1 Step 3", "step3"), ("v2 Step 2", "step2-v2"), ("v2 Step 3", "step3-v2")]


L1_SESSIONS = [("no generator", "step4/L1-nogen"), ("frozen-settings run", "step4/L1-gen-frozen"),
               ("long-context run", "step4/L1-gen-longctx")]


def cross(case: str) -> str:
    import contextlib
    import io

    if case == "L1":
        specs = [f"{lab}={BASE / d}" for lab, d in L1_SESSIONS if (BASE / d).is_dir()]
    else:
        specs = [f"{lab}={BASE / d / case}" for lab, d in SESSIONS if (BASE / d / case).is_dir()]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cross_session.main([case] + specs)
    return buf.getvalue().rstrip("\n")


def cpu_only(run: str) -> str:
    g = BASE / run / "generation"
    rows = [json.loads(x) for x in (g / "generation_log.jsonl").read_text().splitlines() if x.strip()]
    L = ["| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Completion tokens / s | Raw output sha256 | L1 |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    tot = 0.0
    for e in rows:
        tot += e["wall_s"]
        tps = e["completion_tokens"] / e["wall_s"] if e.get("completion_tokens") else 0
        L.append(f"| {e['candidate']} | {e['seed']} | {e['wall_s']:.2f} | {e['prompt_tokens']} | {e['completion_tokens']} | "
                 f"{tps:.1f} | `{e['raw_sha256'][:16]}…` | {e['L1']} |")
    L.append("")
    L.append(f"Total wall-clock for k = {len(rows)}: {tot:.1f} s. Source: `{run}/generation/generation_log.jsonl`.")
    return "\n".join(L)


def endpoints(run: str) -> str:
    p = BASE / run / "generation" / "endpoint_log.jsonl"
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    L = ["| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        L.append(f"| {r['ts']} | {r['method']} | `{r['endpoint']}` | {r['purpose']} | {r.get('seed') or ''} | {r['status']} | {r['duration_s']} |")
    return "\n".join(L)


def render(kind: str, arg: str) -> str:
    if kind == "cross":
        return cross(arg)
    if kind == "cross_v3":   # EVIDENCE.md only: earlier sessions plus v3 (D11)
        import contextlib
        import io
        specs = [f"{lab}={BASE / d / arg}" for lab, d in SESSIONS + [("v3 Step 3", "step3-v3")]
                 if (BASE / d / arg).is_dir()]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cross_session.main([arg] + specs)
        return buf.getvalue().rstrip("\n")
    if kind == "posthoc":    # D11-D14 tables (analysis/posthoc_tables.py)
        import posthoc_tables
        name, _, rest = arg.partition(" ")
        fn = getattr(posthoc_tables, name)
        return fn(*rest.split()) if rest else fn()
    if kind == "excess":     # same table as model_induced, with the D14 label
        d = tables.load(BASE / arg)
        return "\n".join(tables.model_induced_table(d)).replace(
            "(model-induced)", "(excess over matched reference)").replace(
            "no model-induced cost to report", "no excess over a matched reference to report").replace(str(BASE) + "/", "")
    if kind == "cpu_only":
        return cpu_only(arg)
    if kind == "endpoints":
        return endpoints(arg)
    if kind == "file":
        return (BASE / arg).read_text().rstrip("\n")
    if kind == "file_demoted":   # include a Markdown file with its headings pushed down two levels
        return re.sub(r"(?m)^(#+) ", lambda m: "#" * min(6, len(m.group(1)) + 2) + " ",
                      (BASE / arg).read_text().rstrip("\n"))
    d = tables.load(BASE / arg)
    fn = {
        "validation": tables.validation_table,
        "claims": tables.claim_level_counts,
        "generation": tables.generation_table,
        "measurement": tables.measurement_table,
        "decisions": tables.decision_table,
        "model_induced": tables.model_induced_table,
        "power": tables.power_table,
    }[kind]
    out = "\n".join(fn(d))
    return out.replace(str(BASE) + "/", "")


def main(argv):
    src, dst = Path(argv[0]), Path(argv[1])
    text = src.read_text(encoding="utf-8")
    text = re.sub(r"\{\{(\w+):([^}]+)\}\}", lambda m: render(m.group(1), m.group(2).strip()), text)
    dst.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
