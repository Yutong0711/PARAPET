# SPDX-License-Identifier: Apache-2.0
"""Validate stage: does a patch close the weakness and keep required behavior?

A patch is ADMISSIBLE (claim level L4) only if, each in its own fresh JVM:

* it compiles (L2; ``javac --release 17`` on the patched target alone);
* the reproducer no longer fires (L3);
* held-out exploit variant 1 no longer fires;
* held-out exploit variant 2 no longer fires;
* every functional test passes.

A check that cannot be evaluated -- the harness program does not compile
against the patch, the JVM times out or crashes, or no result line is
printed -- counts as failed. Each check is recorded separately with its exact
command and raw output. Probes (legitimate inputs the original accepted) are
run as well and compared with the original afterwards; they do not gate
admissibility.
"""

from __future__ import annotations

import json
from pathlib import Path

from parapet import javatools
from parapet.case import CHECK_NAMES, Case
from parapet.hashing import sha256_text

RESULT_PREFIX = "PARAPET_RESULT "
OUTPUT_KEEP = 8000

CLAIM_LEVELS = {
    "L0": "server answers",
    "L1": "parseable patch",
    "L2": "compiles",
    "L3": "reproducer no longer fires",
    "L4": "admissible (held-out variants and functional tests pass)",
    "L5": "cost fits the declared budget",
}


def parse_result(output: str):
    found = None
    for line in output.splitlines():
        if line.startswith(RESULT_PREFIX):
            try:
                found = json.loads(line[len(RESULT_PREFIX):])
            except json.JSONDecodeError:
                found = None
    return found


def _trim(s: str) -> str:
    return s if len(s) <= OUTPUT_KEEP else s[:OUTPUT_KEEP] + f"\n... [{len(s) - OUTPUT_KEEP} more chars in log]"


def prepare_support(case: Case, root: Path):
    """Compile the case's patch-independent support classes once per run."""
    if not case.support_sources:
        return None, None
    out = root / "support-classes"
    srcs = [case.support_root / s for s in case.support_sources]
    r = javatools.javac(srcs, out, release=case.java_release)
    if not r.ok:
        raise RuntimeError(f"support classes for {case.id} failed to compile: {r.output}")
    return out, {"command": r.command, "ok": r.ok, "duration_s": round(r.duration_s, 3)}


def evaluate_check(name: str, result) -> tuple[bool, str]:
    if result is None:
        return False, "no result line (JVM crash, timeout, or harness error)"
    if name in ("reproducer", "heldout1", "heldout2"):
        if result.get("outcome") == "harness-error":
            return False, f"harness error: {result.get('exception')}"
        if result.get("fired"):
            return False, f"canary fired ({result.get('fired_by')})"
        return True, f"canary did not fire; input {result.get('outcome')}"
    if name == "functional":
        n_pass, n_fail = int(result.get("passed", 0)), int(result.get("failed", 0))
        if n_fail == 0 and n_pass > 0:
            return True, f"{n_pass}/{n_pass} functional tests pass"
        failed = [t["name"] for t in result.get("tests", []) if not t.get("ok")]
        return False, f"{n_fail} of {n_pass + n_fail} functional tests fail: {failed}"
    if name == "probes":
        return True, "probes evaluated (informational)"
    return False, f"unknown check {name}"


def claim_level(compiled: bool, checks: dict) -> str:
    if not compiled:
        return "L1"
    if not checks.get("reproducer", {}).get("passed"):
        return "L2"
    if all(checks.get(n, {}).get("passed") for n in ("heldout1", "heldout2", "functional")):
        return "L4"
    return "L3"


def validate_patch(case: Case, patch_id: str, kind: str, source_text: str, root: Path,
                   support_dir: Path | None, logs_dir: Path, check_timeout: int = 60) -> dict:
    pdir = root / "patches" / patch_id
    src = pdir / "src" / case.target_relpath
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(source_text, encoding="utf-8")
    logs_dir.mkdir(parents=True, exist_ok=True)
    target_classes = pdir / "classes" / "target"
    harness_classes = pdir / "classes" / "harness"

    rec = {
        "patch_id": patch_id,
        "kind": kind,
        "source_sha256": sha256_text(source_text),
        "compile": None,
        "harness_compile": {},
        "checks": {},
        "claim_level": None,
        "admissible": False,
        "classes": {"target": str(target_classes), "harness": str(harness_classes),
                    "support": str(support_dir) if support_dir else None},
    }

    c = javatools.javac([src], target_classes, release=case.java_release)
    (logs_dir / "compile.txt").write_text(f"$ {c.command}\n{c.output}", encoding="utf-8")
    rec["compile"] = {"command": c.command, "ok": c.ok, "duration_s": round(c.duration_s, 3),
                      "output": _trim(c.output)}
    if not c.ok:
        rec["claim_level"] = "L1"
        for name in CHECK_NAMES:
            rec["checks"][name] = {"evaluated": False, "passed": False,
                                   "summary": "not run: patch does not compile"}
        return rec

    programs = {name: case.checks[name] for name in CHECK_NAMES}
    programs["workload"] = case.workload_main
    cp_compile = [target_classes, support_dir]
    for name, main in programs.items():
        main_src = case.harness_sourcepath / (main.replace(".", "/") + ".java")
        r = javatools.javac([main_src], harness_classes, cp=cp_compile,
                            sourcepath=case.harness_sourcepath, release=case.java_release)
        (logs_dir / f"harness_compile_{name}.txt").write_text(f"$ {r.command}\n{r.output}", encoding="utf-8")
        rec["harness_compile"][name] = {"command": r.command, "ok": r.ok,
                                        "duration_s": round(r.duration_s, 3), "output": _trim(r.output)}

    sysprops = {"parapet.fixtures": str(case.fixtures)} if case.fixtures else {}
    for name in CHECK_NAMES:
        if not rec["harness_compile"][name]["ok"]:
            rec["checks"][name] = {"evaluated": False, "passed": False,
                                   "summary": "not run: harness program does not compile against this patch"}
            continue
        r = javatools.java(programs[name], cp=[target_classes, support_dir, harness_classes],
                           sysprops=sysprops, timeout=check_timeout, cwd=pdir)
        (logs_dir / f"check_{name}.txt").write_text(f"$ {r.command}\n{r.output}", encoding="utf-8")
        result = parse_result(r.output)
        passed, summary = evaluate_check(name, result)
        rec["checks"][name] = {
            "command": r.command,
            "exit_ok": r.ok,
            "timed_out": r.timed_out,
            "duration_s": round(r.duration_s, 3),
            "evaluated": result is not None,
            "passed": passed,
            "summary": summary,
            "result": result,
        }

    rec["claim_level"] = claim_level(True, rec["checks"])
    rec["admissible"] = rec["claim_level"] == "L4"
    rec["workload_ready"] = rec["harness_compile"]["workload"]["ok"]
    return rec


def compare_probes(original: dict, patched: dict) -> dict:
    """Inputs the original accepted that the patch now rejects or decodes differently."""
    def rows(v):
        res = (v.get("checks", {}).get("probes") or {}).get("result") or {}
        return {r["probe"]: r for r in res.get("probes", [])}

    o, p = rows(original), rows(patched)
    if not o:
        return {"evaluated": False, "now_rejected": [], "different_result": [],
                "note": "original probes unavailable"}
    if not p:
        return {"evaluated": False, "now_rejected": [], "different_result": [],
                "note": "probes not evaluated for this patch"}
    now_rejected, different = [], []
    for name, orow in o.items():
        prow = p.get(name)
        if orow.get("status") != "accepted" or prow is None:
            continue
        if prow.get("status") != "accepted":
            now_rejected.append({"probe": name, "exception": prow.get("exception")})
        elif prow.get("digest") != orow.get("digest"):
            different.append({"probe": name, "original_digest": orow.get("digest"),
                              "patched_digest": prow.get("digest")})
    return {"evaluated": True, "now_rejected": now_rejected, "different_result": different,
            "probes_total": len(o)}
