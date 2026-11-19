# SPDX-License-Identifier: Apache-2.0
"""Command line: ``python -m parapet run --case C1 --budget <file>``.

``run`` executes the four stages for one case and writes a run directory:

    generation/   prompt, settings, verbatim raw outputs, extracted candidates,
                  generation log (time and tokens per candidate), endpoint log
    validation/   one JSON per patch with every check, its command and result
    measurement/  raw_samples.jsonl (every fork) and summary.json
    decision.json decisions under every budget given
    records/      one hardening record (JSON + Markdown) per patch
    SUMMARY.md    human-readable overview
    run.json      manifest: arguments, commit, environment, hashes, timings

Compilation and measurement happen under a Linux-filesystem work directory
(default ``~/parapet-work/runs``); the run directory is copied into the
repository at the end (``--out``).
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from parapet import __version__
from parapet.budget import load_budget
from parapet.case import load_case
from parapet.decide import decide
from parapet.envinfo import capture as capture_env
from parapet.hashing import sha256_file, sha256_text
from parapet.measure import Arm, load_settings, run_session
from parapet.paths import REPO_ROOT, default_workdir, is_windows_mount
from parapet.prompt import build_prompt, prompt_record
from parapet.record import build_record, write_record
from parapet.validate import compare_probes, prepare_support, validate_patch
from parapet import javatools


def log(msg: str) -> None:
    print(f"[parapet {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def git_info() -> dict:
    def g(*args):
        p = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True)
        return p.stdout.strip()

    dirty = [line for line in g("status", "--porcelain").splitlines()
             if line and not line[3:].startswith("evidence/") and not line[3:].startswith(".coverage")]
    return {"commit": g("rev-parse", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty_outside_evidence": dirty}


def compile_for_workload(case, arm_id: str, source: str, root: Path, support_dir) -> tuple[Path, Path]:
    pdir = root / "patches" / arm_id
    src = pdir / "src" / case.target_relpath
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text(source, encoding="utf-8")
    t, h = pdir / "classes" / "target", pdir / "classes" / "harness"
    r = javatools.javac([src], t, release=case.java_release)
    if not r.ok:
        raise RuntimeError(f"{arm_id}: compile failed: {r.output}")
    main_src = case.harness_sourcepath / (case.workload_main.replace(".", "/") + ".java")
    r = javatools.javac([main_src], h, cp=[t, support_dir], sourcepath=case.harness_sourcepath,
                        release=case.java_release)
    if not r.ok:
        raise RuntimeError(f"{arm_id}: workload compile failed: {r.output}")
    return t, h


def harness_problems(v0: dict) -> list:
    """The unpatched source must fail the checks: every canary must fire on it
    and its functional tests must pass. Otherwise the harness proves nothing."""
    problems = []
    for name in ("reproducer", "heldout1", "heldout2"):
        res = (v0["checks"].get(name) or {}).get("result") or {}
        if not res.get("fired"):
            problems.append(f"{name} does not fire on the unpatched source (outcome={res.get('outcome')}, "
                            f"exception={res.get('exception')})")
    if not (v0["checks"].get("functional") or {}).get("passed"):
        problems.append("functional tests do not pass on the unpatched source")
    return problems


def _rel(p: Path, base: Path) -> str:
    try:
        return str(Path(p).resolve().relative_to(base.resolve()))
    except ValueError:
        return str(p)


def cmd_run(args) -> int:
    t_run = time.time()
    case = load_case(args.case)
    budgets = [load_budget(b) for b in args.budget]
    msettings = load_settings()
    env = capture_env()
    repo = git_info()
    if repo["dirty_outside_evidence"]:
        log(f"WARNING: uncommitted changes outside evidence/: {repo['dirty_outside_evidence']}")

    stamp = time.strftime("%Y%m%dT%H%M%S")
    label = args.label or ("nogen" if args.no_generator else "gen")
    workroot = Path(args.workdir).expanduser() if args.workdir else default_workdir()
    if is_windows_mount(workroot):
        log(f"refusing work directory on a Windows mount: {workroot}")
        return 2
    root = workroot / f"{label}-{case.id}-{stamp}"
    out = root / "out"
    out.mkdir(parents=True, exist_ok=True)
    log(f"case {case.id} ({case.cwe_id}); work dir {root}")
    phases = {}

    original = case.read_target()
    patches = [
        {"id": "V0", "kind": "vulnerable (unpatched baseline)", "source": original,
         "source_path": _rel(case.target_path, REPO_ROOT),
         "mechanism": {"route": "none", "description": "unpatched vulnerable source"}},
        {"id": "CONTROL", "kind": "incomplete control patch (hand-written)",
         "source": case.control_path.read_text(encoding="utf-8"),
         "source_path": _rel(case.control_path, REPO_ROOT),
         "mechanism": {"route": "none (incomplete by design)", "description": case.control_description}},
    ]
    for rid, ref in case.references.items():
        patches.append({"id": rid, "kind": "reference fix (hand-written)",
                        "source": ref.path.read_text(encoding="utf-8"),
                        "source_path": _rel(ref.path, REPO_ROOT),
                        "mechanism": {"route": ref.route, "description": ref.mechanism,
                                      "guidance": list(ref.guidance)}})

    # ---------------------------------------------------------------- Generate
    gen_result = None
    if not args.no_generator:
        t0 = time.time()
        gdir = out / "generation"
        if args.candidates_from:
            src = Path(args.candidates_from)
            shutil.copytree(src, gdir)
            log(f"reusing saved candidates from {src}")
            entries = [json.loads(line) for line in (gdir / "generation_log.jsonl").read_text().splitlines()
                       if line.strip()]
            gen_result = {"candidates": entries,
                          "model": json.loads((gdir / "model.json").read_text()),
                          "prompt": json.loads((gdir / "prompt.json").read_text()),
                          "generator": json.loads((gdir / "settings.json").read_text())["generator"],
                          "reused_from": str(src)}
        else:
            from parapet.generate import generate, load_generation_settings

            gs = load_generation_settings()
            generator = None
            if args.generator_config:
                generator = json.loads(Path(args.generator_config).read_text())
            log("generating candidates")
            gen_result = generate(case, gdir, settings=gs, generator=generator,
                                  allow_hosted_control=args.allow_hosted_control,
                                  id_prefix=args.id_prefix,
                                  power_csv=(gdir / "gpu_power.csv") if args.power_sample else None,
                                  progress=log)
        for e in gen_result["candidates"]:
            if e.get("L1"):
                patches.append({"id": e["candidate"], "kind": "generated candidate",
                                "source": (gdir / e["extracted_path"]).read_text(encoding="utf-8"),
                                "source_path": _rel(gdir / e["extracted_path"], root),
                                "generation": e})
        phases["generate_s"] = round(time.time() - t0, 1)

    # ---------------------------------------------------------------- Validate
    t0 = time.time()
    support_dir, support_info = prepare_support(case, root)
    validations = {}
    for p in patches:
        log(f"validating {p['id']}")
        v = validate_patch(case, p["id"], p["kind"], p["source"], root, support_dir,
                           logs_dir=out / "validation" / "logs" / p["id"])
        validations[p["id"]] = v
        (out / "validation").mkdir(parents=True, exist_ok=True)
        (out / "validation" / f"{p['id']}.json").write_text(json.dumps(v, indent=2), encoding="utf-8")
        log(f"  {p['id']}: {v['claim_level']} " +
            ", ".join(f"{k}={'pass' if c.get('passed') else 'FAIL'}" for k, c in v["checks"].items()))
    probes_cmp = {pid: compare_probes(validations["V0"], v) for pid, v in validations.items()}
    phases["validate_s"] = round(time.time() - t0, 1)
    problems = harness_problems(validations["V0"])
    if problems:
        log(f"HARNESS INVALID for {case.id}: {problems}; stopping before measurement")
        (out / "HARNESS_INVALID.json").write_text(json.dumps(problems, indent=2), encoding="utf-8")
        return 4

    # ---------------------------------------------------------------- Measure
    t0 = time.time()
    arms = [Arm("baseline", "baseline", [Path(validations["V0"]["classes"]["target"]), support_dir,
                                         Path(validations["V0"]["classes"]["harness"])], "V0")]
    aa_t, aa_h = compile_for_workload(case, "V0-AA", original, root, support_dir)
    arms.append(Arm("baseline-AA", "aa", [aa_t, support_dir, aa_h], "V0"))
    measured_ids = []
    for p in patches:
        v = validations[p["id"]]
        if p["id"] in ("V0", "CONTROL") or not v["admissible"] or not v.get("workload_ready"):
            continue
        kind = "reference" if p["id"] in case.references else "candidate"
        matched = None if kind == "reference" else case.match_reference(p["source"])
        p["matched_reference"] = matched
        arms.append(Arm(p["id"], kind, [Path(v["classes"]["target"]), support_dir,
                                        Path(v["classes"]["harness"])], p["id"], matched_reference=matched))
        measured_ids.append(p["id"])
    log(f"measuring arms {[a.id for a in arms]} x {args.forks or msettings['forks_per_arm']} forks")
    summary = run_session(case, arms, msettings, out / "measurement", root / "measure", forks=args.forks,
                          progress=log)
    phases["measure_s"] = round(time.time() - t0, 1)
    nf = summary.get("noise_floor")
    if nf:
        log(f"A/A noise floor: latency {nf['latency_pct']:.2f}%, peak memory {nf['peak_memory_pct']:.2f}%")

    # ---------------------------------------------------------------- Decide
    # Every admissible patch enters the decision (R1, R2, and in generator mode
    # admissible candidates). One that could not be measured has no cost
    # estimate and therefore fails every budget.
    decision_set = [p["id"] for p in patches
                    if p["id"] not in ("V0", "CONTROL") and validations[p["id"]]["admissible"]]
    dec_inputs = [{"patch_id": pid, "admissible": validations[pid]["admissible"],
                   "cost": summary["vs_baseline"].get(pid)} for pid in decision_set]
    decisions = [decide(dec_inputs, b, case.workload_name) for b in budgets]
    (out / "decision.json").write_text(json.dumps(decisions, indent=2), encoding="utf-8")
    for d in decisions:
        log(f"budget {d['profile']}: fitting={d['fitting']} -> {d['statement']}")

    # ---------------------------------------------------------------- Record
    raw_rel = "measurement/raw_samples.jsonl"
    raw_info = {"path": raw_rel, "sha256": summary["raw_samples_sha256"]}
    budget_args = " ".join(f"--budget {shlex.quote(_rel(Path(b), REPO_ROOT))}" for b in args.budget)
    base_cmd = f"python -m parapet run --case {case.id} {budget_args}"
    prec = prompt_record(case)
    for p in patches:
        pid = p["id"]
        v = validations[pid]
        if "generation" in p:
            e = p["generation"]
            model = gen_result["model"]
            generator = {"name": gen_result["generator"].get("model"),
                         "product_name": gen_result["generator"].get("product_name"),
                         "digest": model.get("manifest_digest"), "serving": model.get("serving"),
                         "seed": e.get("seed"), "wall_s": e.get("wall_s"),
                         "prompt_tokens": e.get("prompt_tokens"), "completion_tokens": e.get("completion_tokens"),
                         "raw_output": f"generation/{e['raw_path']}", "raw_sha256": e.get("raw_sha256"),
                         "extraction": e.get("extraction")}
            prompt = gen_result["prompt"]
            reproduce = (f"{base_cmd} --candidates-from <this run>/generation   # re-validate and re-measure "
                         f"the saved candidates\n{base_cmd}   # regenerate (sampling may differ)")
        else:
            generator = {"name": "hand-written reference" if pid in case.references else
                         ("hand-written control" if pid == "CONTROL" else "unpatched original")}
            prompt = None
            reproduce = f"{base_cmd} --no-generator"
        mech = p.get("mechanism")
        if mech is None:
            ref = p.get("matched_reference") or case.match_reference(p["source"])
            mech = {"route": f"same mechanism as {ref} ({case.references[ref].route}) by pre-registered rule",
                    "description": f"matched reference: {ref} — {case.references[ref].mechanism}"}
        record = build_record(
            case=case, patch=p, validation=v, probes_cmp=probes_cmp[pid],
            cost=summary["vs_baseline"].get(pid if pid != "V0" else "__none__"),
            cost_vs_ref=summary["vs_matched_reference"].get(pid),
            raw_samples=raw_info if pid in measured_ids or pid == "V0" else None,
            noise_floor=summary.get("noise_floor"), decisions=decisions, generator=generator,
            prompt=prompt, environment=env, reproduce=reproduce, repo=repo,
            original_source=original, patched_source=p["source"])
        write_record(record, out / "records", pid)

    # ---------------------------------------------------------------- Manifest
    manifest = {
        "parapet_version": __version__,
        "case": case.id,
        "label": label,
        "argv": sys.argv,
        "started_at": t_run,
        "finished_at": time.time(),
        "phases": phases,
        "repo": repo,
        "environment": env,
        "work_dir": str(root),
        "copied_to": None,
        "budgets": [b.as_dict() for b in budgets],
        "measurement_settings": {"path": msettings["_path"], "sha256": msettings["_sha256"]},
        "support_classes": support_info,
        "prompt": prec,
        "generator_used": not args.no_generator,
        "claim_levels": {pid: v["claim_level"] for pid, v in validations.items()},
    }
    if gen_result:
        levels = {}
        for e in gen_result["candidates"]:
            cid = e["candidate"]
            if not e.get("L0"):
                levels[cid] = "none (server did not answer)"
            elif not e.get("L1"):
                levels[cid] = "L0"
            else:
                levels[cid] = validations[cid]["claim_level"]
        manifest["candidate_claim_levels"] = levels
    manifest["l5"] = {d["profile"]: d["fitting"] for d in decisions}
    (out / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out / "SUMMARY.md").write_text(render_summary(case, patches, validations, probes_cmp, summary,
                                                   decisions, gen_result, manifest), encoding="utf-8")

    if args.out:
        dest = Path(args.out)
        if dest.exists():
            log(f"destination {dest} exists; refusing to overwrite")
            return 3
        shutil.copytree(out, dest)
        manifest["copied_to"] = str(dest)
        (dest / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (out / "run.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        log(f"results copied to {dest}")
    log("done")
    return 0


def _ci(c):
    if not c:
        return "—"
    s = f"{c['overhead_pct']:+.2f}% [{c['overhead_pct_lo']:+.2f}, {c['overhead_pct_hi']:+.2f}]"
    if c.get("indistinguishable_from_noise"):
        s += " (indistinguishable)"
    return s


def render_summary(case, patches, validations, probes_cmp, summary, decisions, gen_result, manifest) -> str:
    L = [f"# PARAPET run — {case.id} ({case.cwe_id} {case.cwe_name})", ""]
    L.append(f"- Generator used: {manifest['generator_used']}")
    L.append(f"- Commit: `{manifest['repo']['commit']}` on `{manifest['repo']['branch']}`")
    L.append(f"- Work directory (Linux filesystem): `{manifest['work_dir']}`")
    L.append("")
    if gen_result:
        L.append("## Generation")
        L.append("")
        L.append("| Candidate | Seed | Status | Wall s | Prompt tok | Completion tok | Finish | L1 | Extraction |")
        L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for e in gen_result["candidates"]:
            L.append(f"| {e['candidate']} | {e['seed']} | {e['status']} | {e['wall_s']} | {e.get('prompt_tokens')} | "
                     f"{e.get('completion_tokens')} | {e.get('finish_reason')} | {e.get('L1')} | {e.get('extraction')} |")
        L.append("")
    L.append("## Validation")
    L.append("")
    L.append("| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for p in patches:
        v = validations[p["id"]]
        ck = v["checks"]

        def cell(n):
            c = ck.get(n, {})
            return "pass" if c.get("passed") else ("FAIL" if c.get("evaluated") else "not run")

        nr = probes_cmp[p["id"]]
        rej = ", ".join(x["probe"] for x in nr.get("now_rejected", [])) or "none"
        L.append(f"| {p['id']} | {p['kind']} | {'ok' if v['compile']['ok'] else 'FAIL'} | {cell('reproducer')} | "
                 f"{cell('heldout1')} | {cell('heldout2')} | {cell('functional')} | {v['claim_level']} | {rej} |")
    L.append("")
    L.append("## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)")
    L.append("")
    nf = summary.get("noise_floor")
    if nf:
        L.append(f"A/A noise floor: latency {nf['latency_pct']:.2f}%, peak memory {nf['peak_memory_pct']:.2f}%.")
        L.append("")
    L.append("| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for aid, st in summary["per_arm"].items():
        c = summary["vs_baseline"].get(aid, {})
        r = summary["vs_matched_reference"].get(aid)
        lat = st["latency_ns_per_op_median"]
        L.append(f"| {aid} | {st['valid_forks']} | {lat:.1f} | {st['peak_rss_kib_median']:.0f} | "
                 f"{_ci(c.get('latency'))} | {_ci(c.get('peak_memory'))} | "
                 f"{(r['vs'] + ': ' + _ci(r['latency'])) if r else '—'} |" if lat is not None else
                 f"| {aid} | {st['valid_forks']} | — | — | — | — | — |")
    L.append("")
    L.append(f"Raw samples: `measurement/raw_samples.jsonl` sha256 `{summary['raw_samples_sha256']}`")
    L.append("")
    L.append("## Decisions")
    L.append("")
    for d in decisions:
        L.append(f"- **{d['profile']}** (caps {d['caps']}): fitting {d['fitting'] or 'none'}; {d['statement']}.")
        for r in d["assessed"]:
            if not r["fits"]:
                L.append(f"  - {r['patch_id']}: {'; '.join(r['reasons'])}")
    L.append("")
    return "\n".join(L)


def cmd_prompt(args) -> int:
    case = load_case(args.case)
    print(build_prompt(case))
    print(json.dumps(prompt_record(case), indent=2), file=sys.stderr)
    return 0


def cmd_env(args) -> int:
    print(json.dumps(capture_env(), indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m parapet", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="generate, validate, measure, decide, record for one case")
    r.add_argument("--case", required=True)
    r.add_argument("--budget", action="append", required=True, help="budget file; repeat for several profiles")
    r.add_argument("--no-generator", action="store_true", help="hand-written patches only (no model call)")
    r.add_argument("--candidates-from", help="reuse a saved generation/ directory instead of calling the model")
    r.add_argument("--generator-config", help="JSON file overriding the default generator (controls only)")
    r.add_argument("--allow-hosted-control", action="store_true",
                   help="permit a hosted generator; attribution controls only, never the default path")
    r.add_argument("--id-prefix", default="G", help="candidate id prefix (default G)")
    r.add_argument("--power-sample", action="store_true", help="sample GPU power with nvidia-smi during generation")
    r.add_argument("--forks", type=int, help="override forks per arm (protocol default in settings)")
    r.add_argument("--workdir", help="Linux-filesystem work directory (default ~/parapet-work/runs)")
    r.add_argument("--label", help="label for the run directory")
    r.add_argument("--out", help="copy the run directory here (inside the repository) when done")
    r.set_defaults(func=cmd_run)
    p = sub.add_parser("prompt", help="print the frozen prompt for a case")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_prompt)
    e = sub.add_parser("env", help="print the captured environment")
    e.set_defaults(func=cmd_env)
    args = ap.parse_args(argv)
    return args.func(args)
