# SPDX-License-Identifier: Apache-2.0
"""Cross-session comparison of every measured arm, built only from saved files.

Usage: python cross_session.py <case> <label>=<run_dir> [...]
Prints one Markdown table per case: for each session and each arm, the
latency and peak-memory overhead against that session's baseline with the 95%
bootstrap interval, the session's A/A noise floor, and the budget verdicts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def fmt(c):
    if not c:
        return "—"
    s = f"{c['overhead_pct']:+.2f}% [{c['overhead_pct_lo']:+.2f}, {c['overhead_pct_hi']:+.2f}]"
    return s + (" ≈ noise" if c.get("indistinguishable_from_noise") else "")


def main(argv):
    case = argv[0]
    print(f"| Session | Arm | Latency overhead [95% CI] | Peak-memory overhead [95% CI] | A/A noise floor (lat / mem) | Strict | Lenient |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for spec in argv[1:]:
        label, run = spec.split("=", 1)
        run = Path(run)
        s = json.loads((run / "measurement" / "summary.json").read_text())
        dec = {d["profile"]: d for d in json.loads((run / "decision.json").read_text())}
        nf = s["noise_floor"]
        for aid, c in s["vs_baseline"].items():
            if aid == "baseline-AA":
                continue

            def verdict(profile):
                d = dec[profile]
                row = next((r for r in d["assessed"] if r["patch_id"] == aid), None)
                if row is None:
                    return "—"
                v = "fits" if row["fits"] else "no"
                return v + (" (recommended)" if d["recommended"] == aid else "")

            print(f"| {label} | {aid} | {fmt(c['latency'])} | {fmt(c['peak_memory'])} | "
                  f"{nf['latency_pct']:.2f}% / {nf['peak_memory_pct']:.2f}% | {verdict('strict')} | {verdict('lenient')} |")


if __name__ == "__main__":
    main(sys.argv[1:])
