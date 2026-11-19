# SPDX-License-Identifier: Apache-2.0
"""Post-hoc tables (D11-D14) built from saved files only. Used by build_doc.py.

Functions return Markdown. Nothing here runs a JVM or a model.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
REPO = BASE.parent.parent

C_SESSIONS = [("v1 Step 2", "step2"), ("v1 Step 3", "step3"), ("v2 Step 2", "step2-v2"),
              ("v2 Step 3", "step3-v2"), ("v3 Step 3", "step3-v3")]
L1_SESSIONS = [("no generator", "step4/L1-nogen"), ("frozen-settings run", "step4/L1-gen-frozen"),
               ("long-context run", "step4/L1-gen-longctx")]


def _summary(d: str):
    p = BASE / d / "measurement" / "summary.json"
    return json.loads(p.read_text()) if p.is_file() else None


def _decisions(d: str):
    p = BASE / d / "decision.json"
    return json.loads(p.read_text()) if p.is_file() else None


def _ci(c):
    if not c:
        return "—"
    s = f"{c['overhead_pct']:+.2f}% [{c['overhead_pct_lo']:+.2f}, {c['overhead_pct_hi']:+.2f}]"
    return s + (" ≈ noise" if c.get("indistinguishable_from_noise") else "")


def _overlap(a, b) -> bool:
    return a["overhead_pct_lo"] <= b["overhead_pct_hi"] and b["overhead_pct_lo"] <= a["overhead_pct_hi"]


# ------------------------------------------------------------------ T1

def overlap_table(case: str) -> str:
    """Per arm: does the v3 latency interval overlap each earlier session's interval?"""
    v3 = _summary(f"step3-v3/{case}")
    earlier = [(lab, _summary(f"{d}/{case}")) for lab, d in C_SESSIONS if d != "step3-v3"]
    L = ["| Arm | v3 latency overhead [95% CI] | " + " | ".join(f"overlaps {lab}" for lab, _ in earlier) + " |",
         "| --- | --- | " + " | ".join("---" for _ in earlier) + " |"]
    for aid, c in v3["vs_baseline"].items():
        if aid == "baseline-AA":
            continue
        cells = []
        for _, s in earlier:
            o = (s or {}).get("vs_baseline", {}).get(aid)
            cells.append("not measured" if not o else ("yes" if _overlap(c["latency"], o["latency"]) else "**no**"))
        L.append(f"| {aid} | {_ci(c['latency'])} | " + " | ".join(cells) + " |")
    return "\n".join(L)


# ------------------------------------------------------------------ T4a

def _count_setfeature(text: str) -> int:
    return sum(1 for line in text.splitlines()
               if "setFeature(" in line and "FEATURE_SECURE_PROCESSING" not in line
               and not line.strip().startswith(("//", "*")))


def _method_body(src: str, name: str) -> str:
    m = re.search(r"\b" + re.escape(name) + r"\s*\(", src)
    if not m:
        return ""
    i = src.index("{", m.end())
    depth = 0
    for j in range(i, len(src)):
        depth += src[j] == "{"
        depth -= src[j] == "}"
        if depth == 0:
            return src[i:j + 1]
    return src[i:]


def _sources(case: str) -> dict:
    """patch id -> {relpath: text} for patches measured in the table's session."""
    sys_path = str(REPO)
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from parapet.case import load_case

    k = load_case(case)
    tgt = k.target_relpath
    out = {"baseline": {tgt: k.read_target()}}
    for rid, ref in k.references.items():
        out[rid] = {rel: Path(p).read_text() for rel, p in ref.file_map(tgt).items()}
    gen = BASE / ("step3" if case != "L1" else "step4/L1-gen-longctx") / (case if case != "L1" else "") / "generation"
    for e in (gen / "extracted").glob("G*"):
        out[e.name] = {tgt: (e / Path(tgt).name).read_text()}
    return out


SETFEATURE_NOTES = {
    ("L1", "R1"): ("4 (2 per factory: parse and create)",
                   "upstream helper loops over three feature URIs per feature and stops at the first that "
                   "succeeds; on this JDK the first succeeds, so 2 calls per factory; the workload builds 2 "
                   "factories per operation"),
    ("C2", "P1"): ("0 per operation (4 once, at class load)", "factory configured once and reused"),
}


def feature_table(case: str, session: str) -> str:
    s = _summary(session)
    srcs = _sources(case)
    L = ["| Patch | setFeature calls per workload operation (excl. FEATURE_SECURE_PROCESSING) | Median allocation per operation (bytes) | Latency overhead vs baseline [95% CI] | How the count was derived |",
         "| --- | --- | --- | --- | --- |"]
    for aid, st in s["per_arm"].items():
        if aid == "baseline-AA":
            continue
        pid = st["patch_id"] if aid != "baseline" else "baseline"
        files = srcs.get(pid if pid != "V0" else "baseline", {})
        if (case, aid) in SETFEATURE_NOTES:
            n, how = SETFEATURE_NOTES[(case, aid)]
        elif case == "L1":
            text = "".join(files.values())
            # the workload calls parseDocumentImpl and createDocumentImpl once each per operation
            n_parse = _count_setfeature(_method_body(text, "parseDocumentImpl"))
            n_create = _count_setfeature(_method_body(text, "createDocumentImpl"))
            n = str(n_parse + n_create)
            how = f"static count in parseDocumentImpl ({n_parse}) + createDocumentImpl ({n_create}); no loops"
        else:
            n = str(_count_setfeature("".join(files.values())))
            how = "static count in the target file; every call is on the per-call path" if n != "0" else "no setFeature call"
        c = s["vs_baseline"].get(aid)
        L.append(f"| {aid} | {n} | {st['alloc_bytes_per_op_median']:.0f} | {_ci(c['latency']) if c else '—'} | {how} |")
    p1 = _summary("posthoc/C2-P1-session") if case == "C2" else None
    if p1 and "P1" in p1["per_arm"]:
        n, how = SETFEATURE_NOTES[("C2", "P1")]
        c = p1["vs_baseline"]["P1"]
        L.append(f"| P1 (post-hoc, T2 session) | {n} | {p1['per_arm']['P1']['alloc_bytes_per_op_median']:.0f} | "
                 f"{_ci(c['latency'])} | {how}; measured in its own session against that session's baseline |")
    L.append("")
    L.append(f"Session: `{session}` (allocation and latency from `measurement/summary.json`).")
    return "\n".join(L)


# ------------------------------------------------------------------ T4d

def memory_resolvability() -> str:
    sessions = []
    for case in ("C1", "C2"):
        sessions += [(f"{case} {lab}", f"{d}/{case}", d in ("step2", "step3")) for lab, d in C_SESSIONS]
    sessions += [(f"L1 {lab}", d, False) for lab, d in L1_SESSIONS]
    sessions.append(("C2 post-hoc P1 session", "posthoc/C2-P1-session", False))
    L = ["| Session | A/A peak-memory overhead [95% CI] | Upper bound > 5%? | Strict memory verdicts in this session |",
         "| --- | --- | --- | --- |"]
    for lab, d, v1 in sessions:
        s = _summary(d)
        if not s or "baseline-AA" not in s.get("vs_baseline", {}):
            continue
        aa = s["vs_baseline"]["baseline-AA"]["peak_memory"]
        over = aa["overhead_pct_hi"] > 5.0
        dec = _decisions(d)
        if v1:
            verdict = "v1 memory invalid (D6)"
        elif not over:
            verdict = "resolvable"
        elif dec:
            strict = next(x for x in dec if x["profile"] == "strict")
            verdict = "**not resolvable** for " + ", ".join(r["patch_id"] for r in strict["assessed"])
        else:
            verdict = "**not resolvable** (no decision is made in this session)"
        L.append(f"| {lab} | {_ci(aa)} | {'yes' if over else 'no'} | {verdict} |")
    return "\n".join(L)


# ------------------------------------------------------------------ T2

def p1_report() -> str:
    d = BASE / "posthoc" / "C2-P1-session"
    s = json.loads((d / "measurement" / "summary.json").read_text())
    ex = json.loads((d / "posthoc_comparisons.json").read_text())
    vals = {f.stem: json.loads(f.read_text()) for f in (d / "validation").glob("*.json")}
    probes = json.loads((d / "probes_vs_V0.json").read_text())
    nf = s["noise_floor"]
    L = ["| Arm | Registered checks (claim level) | Inputs now rejected | Median latency (ns/op) | Median alloc (B/op) | Latency vs baseline [95% CI] | Peak memory vs baseline [95% CI] |",
         "| --- | --- | --- | --- | --- | --- | --- |"]
    for aid, st in s["per_arm"].items():
        pid = st["patch_id"]
        v = vals.get(pid, {})
        c = s["vs_baseline"].get(aid, {})
        rej = probes.get(pid, {}).get("now_rejected", [])
        lvl = v.get("claim_level", "—") if aid != "baseline-AA" else "(copy of V0)"
        L.append(f"| {aid} | {lvl} | {len(rej) if aid != 'baseline-AA' else '—'} | {st['latency_ns_per_op_median']:.1f} | "
                 f"{st['alloc_bytes_per_op_median']:.0f} | {_ci(c.get('latency'))} | {_ci(c.get('peak_memory'))} |")
    L.append("")
    L.append(f"A/A noise floor: latency {nf['latency_pct']:.2f}%, peak memory {nf['peak_memory_pct']:.2f}%. "
             f"Raw samples `posthoc/C2-P1-session/measurement/raw_samples.jsonl` sha256 `{s['raw_samples_sha256']}`.")
    L.append("")
    L.append("| Comparison (same session) | Latency [95% CI] | Peak memory [95% CI] |")
    L.append("| --- | --- | --- |")
    for k, c in ex.items():
        L.append(f"| {k.replace('_vs_', ' vs ')} | {_ci(c['latency'])} | {_ci(c['peak_memory'])} |")
    return "\n".join(L)
