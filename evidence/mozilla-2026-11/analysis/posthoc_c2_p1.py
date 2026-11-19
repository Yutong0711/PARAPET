# SPDX-License-Identifier: Apache-2.0
"""T2 (post-hoc, designed after seeing results): C2 arm P1 in its own session.

Arms: baseline (V0), baseline-AA, R1, G2 (saved generated candidate), P1
(posthoc/C2-P1). Every patch goes through the registered C2 checks
(parapet.validate.validate_patch) and the pre-registered measurement protocol
(parapet.measure.run_session). P1 is not a reference fix and enters no
decision table; no budget is applied here. No model is called.

Usage (repository root): python evidence/mozilla-2026-11/analysis/posthoc_c2_p1.py
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from parapet.case import load_case  # noqa: E402
from parapet.cli import compile_for_workload, git_info, harness_problems  # noqa: E402
from parapet.envinfo import capture  # noqa: E402
from parapet.measure import Arm, load_settings, run_session  # noqa: E402
from parapet.stats import ratio_of_medians_ci  # noqa: E402
from parapet.validate import compare_probes, prepare_support, validate_patch  # noqa: E402

EV = REPO / "evidence" / "mozilla-2026-11"
DEST = EV / "posthoc" / "C2-P1-session"


def main() -> int:
    if DEST.exists():
        print(f"{DEST} exists; refusing to overwrite")
        return 3
    case = load_case("C2")
    settings = load_settings()
    root = Path.home() / "parapet-work" / "runs" / f"posthoc-C2-P1-{time.strftime('%Y%m%dT%H%M%S')}"
    out = root / "out"
    out.mkdir(parents=True)
    patches = {
        "V0": case.read_target(),
        "R1": case.references["R1"].path.read_text(encoding="utf-8"),
        "G2": (EV / "step3/C2/generation/extracted/G2/ConfigLoader.java").read_text(encoding="utf-8"),
        "P1": (EV / "posthoc/C2-P1/example/config/ConfigLoader.java").read_text(encoding="utf-8"),
    }
    kinds = {"V0": "vulnerable (unpatched baseline)", "R1": "reference fix (hand-written)",
             "G2": "generated candidate (saved, step3/C2)", "P1": "post-hoc hand-written arm, designed after seeing results"}
    support, _ = prepare_support(case, root)
    vals = {}
    for pid, src in patches.items():
        v = validate_patch(case, pid, kinds[pid], src, root, support, out / "validation" / "logs" / pid)
        vals[pid] = v
        (out / "validation" / f"{pid}.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
        print(pid, v["claim_level"], {k: c.get("passed") for k, c in v["checks"].items()}, flush=True)
    problems = harness_problems(vals["V0"])
    if problems:
        print("HARNESS INVALID", problems)
        return 4
    probes = {pid: compare_probes(vals["V0"], v) for pid, v in vals.items()}
    aa_t, aa_h = compile_for_workload(case, "V0-AA", patches["V0"], root, support)

    def arm(pid, kind, matched=None):
        v = vals[pid]
        return Arm(pid if pid != "V0" else "baseline", kind,
                   [Path(v["classes"]["target"]), support, Path(v["classes"]["harness"])], pid,
                   matched_reference=matched)

    arms = [arm("V0", "baseline"), Arm("baseline-AA", "aa", [aa_t, support, aa_h], "V0"),
            arm("R1", "reference"), arm("G2", "candidate", "R1"), arm("P1", "posthoc")]
    for a in arms[2:]:
        if not vals[a.patch_id]["admissible"]:
            print(f"{a.patch_id} is not admissible; it is still measured for this observation")
    summary = run_session(case, arms, settings, out / "measurement", root / "measure", progress=None)
    bs = settings["bootstrap"]
    kw = {"resamples": bs["resamples"], "confidence": bs["confidence"], "seed": bs["seed"]}
    pa = summary["per_arm"]
    extra = {}
    for a, b in (("P1", "R1"), ("P1", "G2"), ("G2", "R1")):
        if pa[a]["valid"] and pa[b]["valid"]:
            extra[f"{a}_vs_{b}"] = {
                "latency": ratio_of_medians_ci(pa[a]["latency_samples"], pa[b]["latency_samples"], **kw),
                "peak_memory": ratio_of_medians_ci(pa[a]["peak_rss_samples"], pa[b]["peak_rss_samples"], **kw),
            }
    (out / "posthoc_comparisons.json").write_text(json.dumps(extra, indent=2), encoding="utf-8")
    (out / "probes_vs_V0.json").write_text(json.dumps(probes, indent=2), encoding="utf-8")
    (out / "run.json").write_text(json.dumps({
        "label": "T2 post-hoc session (designed after seeing results); P1 is not a reference fix; no decision",
        "argv": sys.argv, "repo": git_info(), "environment": capture(), "work_dir": str(root),
        "measurement_settings": {"path": settings["_path"], "sha256": settings["_sha256"]},
        "claim_levels": {pid: v["claim_level"] for pid, v in vals.items()},
    }, indent=2), encoding="utf-8")
    shutil.copytree(out, DEST)
    print("noise floor", summary["noise_floor"])
    for aid, c in summary["vs_baseline"].items():
        print(aid, "latency %+.2f%% [%+.2f, %+.2f]" % (c["latency"]["overhead_pct"], c["latency"]["overhead_pct_lo"],
                                                     c["latency"]["overhead_pct_hi"]))
    for k, c in extra.items():
        print(k, "latency %+.2f%% [%+.2f, %+.2f]" % (c["latency"]["overhead_pct"], c["latency"]["overhead_pct_lo"],
                                                   c["latency"]["overhead_pct_hi"]))
    print("copied to", DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())
