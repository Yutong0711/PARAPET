# SPDX-License-Identifier: Apache-2.0
"""T3 (post-hoc, supplementary observation; not part of any claim level).

Compiles the L1 library with each patch applied (same layout as validation),
compiles posthoc/L1-dtd-observation/src/obs/ExternalDtdObservation.java
against it, runs it once in a fresh JVM, and records whether the external DTD
named by the document was loaded, not loaded, or the document was rejected.
Patches: V0, CONTROL, R1, R2 (from the case) and G2, G3, G5 (saved candidates
from step4/L1-gen-longctx). No model is called. Writes posthoc/L1-dtd-observation/results.{json,md}.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from parapet import javatools  # noqa: E402
from parapet.case import load_case  # noqa: E402
from parapet.validate import write_sources  # noqa: E402

EV = REPO / "evidence" / "mozilla-2026-11"
OBS = EV / "posthoc" / "L1-dtd-observation"


def main() -> int:
    case = load_case("L1")
    tgt = case.target_relpath
    cand = EV / "step4" / "L1-gen-longctx" / "generation" / "extracted"
    patches = {
        "V0": {tgt: case.read_target()},
        "CONTROL": {tgt: case.control_path.read_text(encoding="utf-8")},
        "R1": {rel: Path(p).read_text(encoding="utf-8")
               for rel, p in case.references["R1"].file_map(tgt).items()},
        "R2": {tgt: case.references["R2"].path.read_text(encoding="utf-8")},
    }
    for g in ("G2", "G3", "G5"):
        patches[g] = {tgt: (cand / g / "BaseXMLBuilder.java").read_text(encoding="utf-8")}
    root = Path.home() / "parapet-work" / "runs" / f"posthoc-L1-dtd-{time.strftime('%Y%m%dT%H%M%S')}"
    rows = []
    for pid, files in patches.items():
        pdir = root / pid
        srcs = write_sources(case, files, pdir / "src")
        c = javatools.javac(srcs, pdir / "classes" / "target", cp=list(case.jars), release=case.java_release)
        if not c.ok:
            rows.append({"patch": pid, "status": "library did not compile", "detail": c.output[-300:]})
            continue
        h = javatools.javac([OBS / "src" / "obs" / "ExternalDtdObservation.java"], pdir / "classes" / "obs",
                            cp=[pdir / "classes" / "target", *case.jars], release=case.java_release)
        if not h.ok:
            rows.append({"patch": pid, "status": "observation did not compile", "detail": h.output[-300:]})
            continue
        r = javatools.java("obs.ExternalDtdObservation", cp=[pdir / "classes" / "target", pdir / "classes" / "obs",
                                                             *case.jars], timeout=60, cwd=pdir)
        line = next((ln for ln in r.output.splitlines() if ln.startswith("PARAPET_OBS ")), None)
        res = json.loads(line[len("PARAPET_OBS "):]) if line else {"status": "no result", "detail": r.output[-300:]}
        res.update({"patch": pid, "command": r.command})
        rows.append(res)
        print(pid, res["status"], "|", res["detail"][:160], flush=True)
    OBS.mkdir(parents=True, exist_ok=True)
    (OBS / "results.json").write_text(json.dumps({"work_dir": str(root), "rows": rows}, indent=2), encoding="utf-8")
    md = ["| Patch | Observation | Detail (truncated) |", "| --- | --- | --- |"]
    for x in rows:
        md.append(f"| {x['patch']} | {x['status']} | {x['detail'][:160].replace('|', '/')} |")
    (OBS / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
