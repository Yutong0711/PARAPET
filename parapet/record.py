# SPDX-License-Identifier: Apache-2.0
"""Hardening records: one JSON + one Markdown file per patch.

A record carries: the weakness (CWE), the mechanism route, the diff against
the vulnerable source, each check with its command and result, the inputs the
patch now rejects, the cost with its interval and the raw-sample hash, the
budget hash and decision, the generator (name and digest, or "hand-written
reference"), the serving stack, the prompt hash, the environment, a
reproduce command, and the repository commit.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path

RECORD_SCHEMA = "parapet.hardening-record/1"
REQUIRED_FIELDS = (
    "schema", "case", "weakness", "patch", "mechanism", "diff", "checks", "claim_level",
    "inputs_now_rejected", "cost", "budgets", "generator", "prompt", "environment",
    "reproduce", "repo",
)


def unified_diff(original: str, patched: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True), patched.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}"))


def build_record(*, case, patch: dict, validation: dict, probes_cmp: dict, cost: dict | None,
                 cost_vs_ref: dict | None, raw_samples: dict | None, noise_floor: dict | None,
                 decisions: list, generator: dict, prompt: dict | None, environment: dict,
                 reproduce: str, repo: dict, original_source: str, patched_source: str,
                 diff: str | None = None) -> dict:
    checks = []
    comp = validation.get("compile") or {}
    checks.append({"name": "compile", "command": comp.get("command"), "passed": bool(comp.get("ok")),
                   "summary": "compiles" if comp.get("ok") else "does not compile"})
    for name in ("reproducer", "heldout1", "heldout2", "functional", "probes"):
        c = validation["checks"].get(name, {})
        checks.append({"name": name, "command": c.get("command"), "passed": bool(c.get("passed")),
                       "evaluated": bool(c.get("evaluated")), "summary": c.get("summary"),
                       "result": c.get("result")})
    budgets = []
    for d in decisions:
        row = next((r for r in d["assessed"] if r["patch_id"] == patch["id"]), None)
        budgets.append({
            "profile": d["profile"], "path": d["budget_path"], "sha256": d["budget_sha256"],
            "caps": d["caps"], "fits": bool(row and row["fits"]),
            "reasons": row["reasons"] if row else ["not assessed"],
            "recommended_patch": d["recommended"], "this_patch_recommended": d["recommended"] == patch["id"],
            "claim_level": "L5" if (row and row["fits"]) else validation.get("claim_level"),
        })
    return {
        "schema": RECORD_SCHEMA,
        "case": {"id": case.id, "title": case.title},
        "weakness": {"cwe": case.cwe_id, "name": case.cwe_name},
        "patch": {"id": patch["id"], "kind": patch["kind"], "source_sha256": validation.get("source_sha256"),
                  "source_path": patch.get("source_path")},
        "mechanism": patch.get("mechanism"),
        "diff": diff if diff is not None else unified_diff(original_source, patched_source, case.target_relpath),
        "checks": checks,
        "claim_level": validation.get("claim_level"),
        "admissible": bool(validation.get("admissible")),
        "inputs_now_rejected": probes_cmp,
        "cost": {
            "vs_baseline": cost,
            "vs_matched_reference": cost_vs_ref,
            "noise_floor_pct": noise_floor,
            "raw_samples": raw_samples,
        },
        "budgets": budgets,
        "generator": generator,
        "prompt": prompt,
        "environment": environment,
        "reproduce": reproduce,
        "repo": repo,
    }


def _fmt_ci(c: dict | None) -> str:
    if not c:
        return "not measured"
    s = f"{c['overhead_pct']:+.2f}% (95% CI {c['overhead_pct_lo']:+.2f}% to {c['overhead_pct_hi']:+.2f}%)"
    if c.get("indistinguishable_from_noise"):
        s += " — indistinguishable from the A/A noise floor"
    return s


def render_markdown(r: dict) -> str:
    L = []
    L.append(f"# Hardening record — {r['case']['id']} / {r['patch']['id']}")
    L.append("")
    L.append(f"- **Weakness:** {r['weakness']['cwe']} {r['weakness']['name']}")
    L.append(f"- **Case:** {r['case']['title']}")
    L.append(f"- **Patch:** `{r['patch']['id']}` ({r['patch']['kind']}), source sha256 `{r['patch']['source_sha256']}`")
    m = r.get("mechanism") or {}
    L.append(f"- **Mechanism route:** {m.get('route', 'n/a')} — {m.get('description', '')}")
    L.append(f"- **Claim level:** {r['claim_level']} (admissible: {r['admissible']})")
    g = r["generator"]
    L.append(f"- **Generator:** {g.get('name')}" + (f", digest `{g.get('digest')}`" if g.get("digest") else ""))
    if g.get("serving"):
        L.append(f"- **Serving stack:** {g['serving']}")
    if r.get("prompt"):
        L.append(f"- **Prompt sha256:** `{r['prompt'].get('prompt_sha256')}`")
    L.append(f"- **Repository commit:** `{r['repo'].get('commit')}` (branch `{r['repo'].get('branch')}`)")
    L.append("")
    L.append("## Checks")
    L.append("")
    L.append("| Check | Passed | Summary | Command |")
    L.append("| --- | --- | --- | --- |")
    for c in r["checks"]:
        cmd = (c.get("command") or "").replace("|", "\\|")
        L.append(f"| {c['name']} | {'yes' if c['passed'] else 'NO'} | {c.get('summary') or ''} | `{cmd}` |")
    L.append("")
    L.append("## Inputs the original accepted that this patch now rejects")
    L.append("")
    nr = r["inputs_now_rejected"]
    if not nr.get("evaluated"):
        L.append(f"Not evaluated: {nr.get('note')}")
    else:
        if nr["now_rejected"]:
            for x in nr["now_rejected"]:
                L.append(f"- `{x['probe']}` — {x.get('exception')}")
        else:
            L.append("- none")
        if nr["different_result"]:
            L.append("")
            L.append("Accepted with a different result than the original:")
            for x in nr["different_result"]:
                L.append(f"- `{x['probe']}`")
    L.append("")
    L.append("## Cost on the workload")
    L.append("")
    cost = r["cost"]
    vb = cost.get("vs_baseline")
    L.append(f"- Latency overhead vs unpatched baseline: {_fmt_ci(vb and vb.get('latency'))}")
    L.append(f"- Peak-memory overhead vs unpatched baseline: {_fmt_ci(vb and vb.get('peak_memory'))}")
    vr = cost.get("vs_matched_reference")
    if vr:
        L.append(f"- Latency vs matched reference {vr['vs']} (model-induced cost): {_fmt_ci(vr.get('latency'))}")
        L.append(f"- Peak memory vs matched reference {vr['vs']}: {_fmt_ci(vr.get('peak_memory'))}")
    nf = cost.get("noise_floor_pct")
    if nf:
        L.append(f"- A/A noise floor: latency {nf['latency_pct']:.2f}%, peak memory {nf['peak_memory_pct']:.2f}%")
    rs = cost.get("raw_samples")
    if rs:
        L.append(f"- Raw samples: `{rs.get('path')}` sha256 `{rs.get('sha256')}`")
    L.append("")
    L.append("## Budget decisions")
    L.append("")
    for b in r["budgets"]:
        verdict = "fits" if b["fits"] else "does not fit"
        L.append(f"- **{b['profile']}** (caps {b['caps']}, budget sha256 `{b['sha256'][:16]}…`): {verdict}"
                 + ("" if b["fits"] else f" — {'; '.join(b['reasons'])}")
                 + f". Recommended patch under this budget: `{b['recommended_patch']}`.")
    L.append("")
    L.append("## Diff")
    L.append("")
    L.append("```diff")
    L.append(r["diff"].rstrip("\n") or "(no change)")
    L.append("```")
    L.append("")
    L.append("## Environment")
    L.append("")
    env = r["environment"]
    for k in ("os", "kernel", "cpu", "logical_cpus", "ram_gib", "gpu", "jdk", "python"):
        if k in env:
            L.append(f"- {k}: {env[k]}")
    L.append("")
    L.append("## Reproduce")
    L.append("")
    L.append("```bash")
    L.append(r["reproduce"])
    L.append("```")
    L.append("")
    return "\n".join(L)


def write_record(record: dict, out_dir: Path, name: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    jp, mp = out_dir / f"{name}.json", out_dir / f"{name}.md"
    jp.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    mp.write_text(render_markdown(record), encoding="utf-8")
    return jp, mp
