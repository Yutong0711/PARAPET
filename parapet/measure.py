# SPDX-License-Identifier: Apache-2.0
"""Measure stage: what a patch costs on the project's own workload.

Thin runner, written instead of reusing PerfOrch's ``refine_test``. That
backend writes a single ``Main.java``, wraps ``main`` in an in-process loop,
and reports cmdbench averages over 3 iterations; it has no notion of forked
JVMs per arm, interleaved arms, discarded warm-up, or per-fork raw samples,
and adapting it would mean editing ``projects/`` (not allowed) or rewriting
it around the outside. Compilation and validation runs do reuse PerfOrch's
``core.run_with_timeout`` (see parapet.javatools).

Protocol (parapet/settings/measurement.yaml): for fork index i, every arm is
run once in its own JVM, in an order shuffled with a seeded RNG, so arms are
interleaved in time. Inside each JVM the case workload runs warm-up rounds
(discarded) and measured rounds (timed with System.nanoTime). Each fork yields
one latency sample (mean ns/op over measured rounds) and one peak-memory
sample (ru_maxrss of that JVM, from wait4). Every raw sample is written to
``raw_samples.jsonl`` before any statistic is computed.
"""

from __future__ import annotations

import json
import os
import random
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from parapet.hashing import sha256_file
from parapet.javatools import classpath
from parapet.paths import SETTINGS_DIR
from parapet.stats import median, noise_floor_pct, ratio_of_medians_ci

WORKLOAD_PREFIX = "PARAPET_WORKLOAD "
GNU_TIME = "/usr/bin/time"


def require_gnu_time() -> None:
    import shutil as _sh
    if not (Path(GNU_TIME).is_file() and _sh.which(GNU_TIME)):
        raise RuntimeError(f"{GNU_TIME} (GNU time) is required to measure the JVM's own peak RSS")


def load_settings(path: Path | None = None) -> dict:
    p = path or (SETTINGS_DIR / "measurement.yaml")
    data = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
    data["_path"] = str(p)
    data["_sha256"] = sha256_file(Path(p))
    return data


@dataclass
class Arm:
    id: str
    kind: str              # baseline | aa | reference | candidate
    cp: list
    patch_id: str
    matched_reference: str | None = None
    extra: dict = field(default_factory=dict)


def schedule(arm_ids: list, forks: int, seed: int) -> list:
    order = []
    for i in range(forks):
        ids = list(arm_ids)
        random.Random(seed * 1000 + i).shuffle(ids)
        order.extend((i, pos, a) for pos, a in enumerate(ids))
    return order


def run_fork(arm: Arm, main: str, settings: dict, ops: int, fork_dir: Path) -> dict:
    fork_dir.mkdir(parents=True, exist_ok=True)
    rss_file = fork_dir / "maxrss_kib.txt"
    # Peak RSS comes from GNU time, which forks the JVM from its own small
    # process and reports that child's ru_maxrss. Taking ru_maxrss from our
    # own wait4 is wrong: Linux carries the parent's (this Python process's)
    # RSS high-water mark into the child at exec, so wait4 reports
    # max(parent high-water, JVM peak). See evidence/DEVIATIONS.md, D6.
    argv = [GNU_TIME, "-f", "%M", "-o", str(rss_file)]
    if settings.get("cpu_affinity"):
        argv += ["taskset", "-c", str(settings["cpu_affinity"])]
    argv += ["java", *settings["jvm_flags"], "-cp", classpath(*arm.cp), main,
             str(settings["warmup_rounds"]), str(settings["measured_rounds"]), str(ops)]
    out_path, err_path = fork_dir / "stdout.txt", fork_dir / "stderr.txt"
    timed_out = {"v": False}
    started = time.time()
    t0 = time.monotonic()
    with open(out_path, "w") as fo, open(err_path, "w") as fe:
        proc = subprocess.Popen(argv, stdout=fo, stderr=fe, start_new_session=True, cwd=str(fork_dir))

        def _kill():
            timed_out["v"] = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        timer = threading.Timer(settings["fork_timeout_s"], _kill)
        timer.start()
        try:
            _, status, rusage = os.wait4(proc.pid, 0)
        finally:
            timer.cancel()
        proc.returncode = os.waitstatus_to_exitcode(status)
    wall = time.monotonic() - t0
    stdout = out_path.read_text(errors="replace")
    stderr = err_path.read_text(errors="replace")
    try:
        jvm_maxrss = int(rss_file.read_text().split()[-1])
    except (OSError, ValueError, IndexError):
        jvm_maxrss = None
    sample = {
        "arm": arm.id, "kind": arm.kind, "patch_id": arm.patch_id,
        "argv": argv, "started_at": started, "wall_s": wall,
        "exit_code": proc.returncode, "timed_out": timed_out["v"],
        "maxrss_kib": jvm_maxrss, "maxrss_source": "GNU time %M (JVM process only)",
        "maxrss_kib_wait4_includes_parent": rusage.ru_maxrss,
        "user_s": rusage.ru_utime, "sys_s": rusage.ru_stime,
        "ok": False, "ns_per_op": None, "round_ns": None, "alloc_bytes_per_op": None,
        "stderr_tail": stderr[-500:],
    }
    payload = None
    for line in stdout.splitlines():
        if line.startswith(WORKLOAD_PREFIX):
            try:
                payload = json.loads(line[len(WORKLOAD_PREFIX):])
            except json.JSONDecodeError:
                payload = None
    if payload and proc.returncode == 0 and not timed_out["v"] and jvm_maxrss is not None:
        rounds = payload["round_ns"]
        if len(rounds) == settings["measured_rounds"]:
            sample["round_ns"] = rounds
            sample["ns_per_op"] = sum(rounds) / (len(rounds) * payload["ops"])
            sample["alloc_bytes_per_op"] = payload.get("alloc_bytes_per_op")
            sample["ok"] = True
    return sample


def run_session(case, arms: list, settings: dict, out_dir: Path, work_dir: Path,
                forks: int | None = None, progress=print) -> dict:
    """Run every arm, interleaved; write raw samples; return the summary."""
    forks = forks or settings["forks_per_arm"]
    require_gnu_time()
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "raw_samples.jsonl"
    by_id = {a.id: a for a in arms}
    plan = schedule([a.id for a in arms], forks, settings["schedule_seed"])
    t_start = time.time()
    with open(raw_path, "w") as raw:
        for n, (i, pos, aid) in enumerate(plan):
            s = run_fork(by_id[aid], case.workload_main, settings, case.ops_per_round,
                         work_dir / "forks" / aid / f"{i:03d}")
            s["fork_index"], s["position"], s["seq"] = i, pos, n
            raw.write(json.dumps(s) + "\n")
            raw.flush()
            if progress and (n + 1) % max(1, len(arms)) == 0:
                progress(f"  measured fork {i + 1}/{forks} of {len(arms)} arms")
    summary = summarize(raw_path, arms, settings)
    summary["session"] = {
        "started_at": t_start, "finished_at": time.time(), "forks_per_arm": forks,
        "arms": [a.id for a in arms], "workload": case.workload_name,
        "workload_main": case.workload_main, "ops_per_round": case.ops_per_round,
        "work_dir": str(work_dir), "settings_path": settings["_path"],
        "settings_sha256": settings["_sha256"],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def summarize(raw_path: Path, arms: list, settings: dict) -> dict:
    samples = [json.loads(line) for line in Path(raw_path).read_text().splitlines() if line.strip()]
    bs = settings["bootstrap"]
    kw = {"resamples": bs["resamples"], "confidence": bs["confidence"], "seed": bs["seed"]}
    per_arm = {}
    for a in arms:
        ok = [s for s in samples if s["arm"] == a.id and s["ok"]]
        bad = [s for s in samples if s["arm"] == a.id and not s["ok"]]
        lat = [s["ns_per_op"] for s in ok]
        mem = [s["maxrss_kib"] for s in ok]
        alloc = [s["alloc_bytes_per_op"] for s in ok if s["alloc_bytes_per_op"] is not None]
        per_arm[a.id] = {
            "kind": a.kind, "patch_id": a.patch_id, "matched_reference": a.matched_reference,
            "valid_forks": len(ok), "failed_forks": len(bad),
            "failed_fork_reasons": [{"fork_index": s["fork_index"], "exit_code": s["exit_code"],
                                     "timed_out": s["timed_out"], "stderr_tail": s["stderr_tail"]} for s in bad],
            "valid": len(ok) >= settings["min_valid_forks"],
            "latency_ns_per_op_median": median(lat) if lat else None,
            "peak_rss_kib_median": median(mem) if mem else None,
            "alloc_bytes_per_op_median": median(alloc) if alloc else None,
            "latency_samples": lat, "peak_rss_samples": mem,
        }
    base = per_arm.get("baseline")
    comps = {}
    noise = None
    if base and base["valid"]:
        for aid, st in per_arm.items():
            if aid == "baseline" or not st["valid"]:
                continue
            comps[aid] = {
                "vs": "baseline",
                "latency": ratio_of_medians_ci(st["latency_samples"], base["latency_samples"], **kw),
                "peak_memory": ratio_of_medians_ci(st["peak_rss_samples"], base["peak_rss_samples"], **kw),
            }
        if "baseline-AA" in comps:
            aa = comps["baseline-AA"]
            noise = {"latency_pct": noise_floor_pct(aa["latency"]),
                     "peak_memory_pct": noise_floor_pct(aa["peak_memory"])}
    for aid, c in comps.items():
        if noise:
            c["latency"]["indistinguishable_from_noise"] = abs(c["latency"]["overhead_pct"]) < noise["latency_pct"]
            c["peak_memory"]["indistinguishable_from_noise"] = (
                abs(c["peak_memory"]["overhead_pct"]) < noise["peak_memory_pct"])
    vs_ref = {}
    for a in arms:
        if a.kind != "candidate" or not a.matched_reference:
            continue
        st, ref = per_arm.get(a.id), per_arm.get(a.matched_reference)
        if st and ref and st["valid"] and ref["valid"]:
            vs_ref[a.id] = {
                "vs": a.matched_reference,
                "latency": ratio_of_medians_ci(st["latency_samples"], ref["latency_samples"], **kw),
                "peak_memory": ratio_of_medians_ci(st["peak_rss_samples"], ref["peak_rss_samples"], **kw),
            }
            if noise:
                vs_ref[a.id]["latency"]["indistinguishable_from_noise"] = (
                    abs(vs_ref[a.id]["latency"]["overhead_pct"]) < noise["latency_pct"])
                vs_ref[a.id]["peak_memory"]["indistinguishable_from_noise"] = (
                    abs(vs_ref[a.id]["peak_memory"]["overhead_pct"]) < noise["peak_memory_pct"])
    return {
        "raw_samples": str(raw_path.name),
        "raw_samples_sha256": sha256_file(Path(raw_path)),
        "n_samples": len(samples),
        "per_arm": per_arm,
        "vs_baseline": comps,
        "vs_matched_reference": vs_ref,
        "noise_floor": noise,
    }
