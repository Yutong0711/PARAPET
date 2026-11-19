# SPDX-License-Identifier: Apache-2.0
"""Build the evidence tables from saved run directories. Reads files only.

Every number in the generated Markdown comes from a file under
evidence/mozilla-2026-11/ (validation/*.json, measurement/summary.json,
decision.json, generation/generation_log.jsonl, generation/gpu_power.csv).

Usage: python evidence/mozilla-2026-11/analysis/tables.py <run_dir> [<run_dir> ...] > out.md
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path

LEVELS = ["L0", "L1", "L2", "L3", "L4"]


def load(run: Path) -> dict:
    d = {"run": run, "manifest": json.loads((run / "run.json").read_text())}
    d["validation"] = {f.stem: json.loads(f.read_text()) for f in sorted((run / "validation").glob("*.json"))}
    d["summary"] = json.loads((run / "measurement" / "summary.json").read_text())
    d["decisions"] = json.loads((run / "decision.json").read_text())
    g = run / "generation" / "generation_log.jsonl"
    d["gen"] = [json.loads(x) for x in g.read_text().splitlines() if x.strip()] if g.is_file() else None
    return d


def ci(c, digits=2):
    if not c:
        return "—"
    s = f"{c['overhead_pct']:+.{digits}f}% [{c['overhead_pct_lo']:+.{digits}f}, {c['overhead_pct_hi']:+.{digits}f}]"
    return s + (" ≈ noise" if c.get("indistinguishable_from_noise") else "")


def validation_table(d) -> list:
    L = ["| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    v0 = d["validation"]["V0"]
    v0p = {r["probe"]: r for r in (v0["checks"]["probes"].get("result") or {}).get("probes", [])}
    order = ["V0", "CONTROL", "R1", "R2"] + sorted(k for k in d["validation"] if k.startswith(("G", "H")))
    for pid in order:
        v = d["validation"].get(pid)
        if not v:
            continue

        def cell(n):
            c = v["checks"].get(n, {})
            if not c.get("evaluated"):
                return "not run"
            if n in ("reproducer", "heldout1", "heldout2"):
                r = c.get("result") or {}
                return "blocked" if c["passed"] else f"FIRES ({r.get('fired_by')})"
            return c.get("summary", "")

        pr = {r["probe"]: r for r in ((v["checks"].get("probes") or {}).get("result") or {}).get("probes", [])}
        rej = [n for n, r in v0p.items() if r["status"] == "accepted" and pr.get(n, {}).get("status") not in (None, "accepted")]
        rej_s = (f"{len(rej)}/{len(v0p)}: " + ", ".join(rej)) if pr else "not run"
        if pr and not rej:
            rej_s = f"0/{len(v0p)}"
        L.append(f"| {pid} | {'yes' if v['compile']['ok'] else 'NO'} | {cell('reproducer')} | {cell('heldout1')} | "
                 f"{cell('heldout2')} | {cell('functional')} | {v['claim_level']} | {rej_s} |")
    return L


def measurement_table(d) -> list:
    s = d["summary"]
    nf = s["noise_floor"]
    L = [f"Session: {s['session']['forks_per_arm']} forks per arm, arms {', '.join(s['session']['arms'])}; "
         f"raw samples `{s['raw_samples']}` sha256 `{s['raw_samples_sha256']}`.",
         "",
         f"A/A noise floor: latency **{nf['latency_pct']:.2f}%**, peak memory **{nf['peak_memory_pct']:.2f}%**.",
         "",
         "| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |",
         "| --- | --- | --- | --- | --- | --- | --- |"]
    for aid, st in s["per_arm"].items():
        c = s["vs_baseline"].get(aid, {})
        L.append(f"| {aid} | {st['valid_forks']}/{st['valid_forks'] + st['failed_forks']} | "
                 f"{st['latency_ns_per_op_median']:.1f} | {st['peak_rss_kib_median']:.0f} | "
                 f"{st['alloc_bytes_per_op_median']:.0f} | {ci(c.get('latency'))} | {ci(c.get('peak_memory'))} |")
    return L


def model_induced_table(d) -> list:
    s = d["summary"]
    if not s["vs_matched_reference"]:
        return ["No admissible generated candidate, so no model-induced cost to report."]
    L = ["| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |",
         "| --- | --- | --- | --- | --- |"]
    for aid, r in s["vs_matched_reference"].items():
        L.append(f"| {aid} | {r['vs']} | {ci(s['vs_baseline'][aid]['latency'])} | {ci(r['latency'])} | {ci(r['peak_memory'])} |")
    return L


def decision_table(d) -> list:
    L = ["| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |",
         "| --- | --- | --- | --- | --- | --- |"]
    for dec in d["decisions"]:
        why = "; ".join(f"{r['patch_id']}: {', '.join(r['reasons'])}" for r in dec["assessed"] if not r["fits"]) or "—"
        L.append(f"| {dec['profile']} (`{dec['budget_sha256'][:12]}…`) | {dec['caps']['latency_overhead_pct']}, "
                 f"{dec['caps']['peak_memory_overhead_pct']} | {', '.join(r['patch_id'] for r in dec['assessed'])} | "
                 f"{', '.join(dec['fitting']) or 'none'} | {dec['recommended'] or 'none'} | {why} |")
    return L


def generation_table(d) -> list:
    L = ["| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |",
         "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for e in d["gen"]:
        cid = e["candidate"]
        if not e.get("L0"):
            lvl = "none (no answer)"
        elif not e.get("L1"):
            lvl = "L0"
        else:
            lvl = d["validation"][cid]["claim_level"]
        L.append(f"| {cid} | {e['seed']} | {e['wall_s']:.2f} | {e.get('prompt_tokens')} | {e.get('completion_tokens')} | "
                 f"{e.get('finish_reason')} | `{e['raw_sha256'][:16]}…` | {lvl} |")
    return L


def claim_level_counts(d) -> list:
    k = len(d["gen"])
    reached = {lv: 0 for lv in LEVELS}
    for e in d["gen"]:
        cid = e["candidate"]
        if not e.get("L0"):
            continue
        top = "L0" if not e.get("L1") else d["validation"][cid]["claim_level"]
        for lv in LEVELS:
            if LEVELS.index(lv) <= LEVELS.index(top):
                reached[lv] += 1
    l5 = {dec["profile"]: sum(1 for r in dec["assessed"] if r["fits"] and r["patch_id"].startswith("G"))
          for dec in d["decisions"]}
    row = " | ".join(f"{reached[lv]}/{k}" for lv in LEVELS)
    return ["| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | "
            "L4 admissible | L5 fits strict | L5 fits lenient |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            f"| {d['manifest']['case']} | {row} | {l5.get('strict', 0)}/{k} | {l5.get('lenient', 0)}/{k} |"]


def power_table(d) -> list:
    p = d["run"] / "generation" / "gpu_power.csv"
    if not p.is_file():
        return []
    rows = [r for r in csv.reader(p.open()) if r and not r[0].startswith("timestamp")]
    P = [(dt.datetime.strptime(r[0].strip(), "%Y/%m/%d %H:%M:%S.%f"), float(r[1])) for r in rows]
    L = ["| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |",
         "| --- | --- | --- | --- | --- |"]
    for e in d["gen"]:
        t0 = dt.datetime.fromtimestamp(e["started_at"])
        t1 = t0 + dt.timedelta(seconds=e["wall_s"])
        w = [x for x in P if t0 <= x[0] <= t1]
        if len(w) < 2:
            L.append(f"| {e['candidate']} | {len(w)} | — | — | — |")
            continue
        energy = sum((w[i + 1][0] - w[i][0]).total_seconds() * (w[i][1] + w[i + 1][1]) / 2 for i in range(len(w) - 1))
        L.append(f"| {e['candidate']} | {len(w)} | {sum(x[1] for x in w) / len(w):.1f} | {max(x[1] for x in w):.1f} | {energy:.0f} |")
    idle = [x[1] for x in P[:3]]
    L.append("")
    L.append(f"First samples before the first request (board idle plus desktop): {', '.join(f'{x:.1f}' for x in idle)} W. "
             f"{len(P)} samples at 200 ms from `{p.relative_to(d['run'])}`.")
    return L


def main(argv):
    for run in map(Path, argv):
        d = load(run)
        m = d["manifest"]
        print(f"### {m['case']} — `{run}`")
        print()
        print(f"Commit `{m['repo']['commit'][:12]}`, generator used: {m['generator_used']}, "
              f"phases {m['phases']}.")
        print()
        if d["gen"]:
            print("**Claim levels (generated candidates, k = %d)**" % len(d["gen"]))
            print()
            print("\n".join(claim_level_counts(d)))
            print()
            print("**Generation (time and tokens per candidate)**")
            print()
            print("\n".join(generation_table(d)))
            print()
        print("**Validation**")
        print()
        print("\n".join(validation_table(d)))
        print()
        print("**Measurement**")
        print()
        print("\n".join(measurement_table(d)))
        print()
        if d["gen"]:
            print("**Model-induced cost (candidate vs the reference fix with the same mechanism)**")
            print()
            print("\n".join(model_induced_table(d)))
            print()
        print("**Budget decisions**")
        print()
        print("\n".join(decision_table(d)))
        print()
        pt = power_table(d) if d["gen"] else []
        if pt:
            print("**GPU board power during generation (Step 6)**")
            print()
            print("\n".join(pt))
            print()


if __name__ == "__main__":
    main(sys.argv[1:])
