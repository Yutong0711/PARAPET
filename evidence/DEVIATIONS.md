# Deviations log — mozilla/local-slice

Every change to pre-registered material after the `prereg:` commit is
recorded here with its reason and time, and results are reported for both
versions. Section 1 records things a reader should know that happened BEFORE
the pre-registration commit.

## 1. Disclosures made before pre-registration

**P1. Development runs of the workload driver before pre-registration
(2026-11-18, ~16:47–16:58 PST).** While authoring the harness, I executed the
case checks and the workload driver to debug them. For C1 this printed
single-JVM timings (5 or 20 measured rounds) for the unpatched source, R1, R2
and the control patch; the R2 run was visibly faster than the baseline. For C2
the workload was timed only on the unpatched source, to choose
`ops_per_round` (600); C2's R1/R2/control workload runs were executed only to
confirm they start, with timing output suppressed. None of these runs is
evidence and none was saved. The budget caps committed in the prereg commit
(strict 5%/5%, lenient 25%/25%) were chosen before any of these runs; this
cannot be proven from the repository and is stated here so a reader can
discount accordingly.

**P2. C2 reference fixes revised before pre-registration (~16:55 PST).** After
reading the current OWASP XXE Prevention Cheat Sheet, R1 was changed from
`disallow-doctype-decl` + `setXIncludeAware(false)` to the cheat sheet's exact
DOM snippet (`disallow-doctype-decl` + `FEATURE_SECURE_PROCESSING`), and R2
from an `EntityResolver` returning empty content to one that throws
`SAXException`, as the cheat sheet states, plus `FEATURE_SECURE_PROCESSING`.
Reason: match published guidance exactly. No timing of either version was
looked at.

**P3. A harness defect found and fixed before pre-registration (~17:01 PST).**
A plumbing test showed C1's payload checks counted an unreadable fixture file
as "input rejected, canary did not fire", which would have passed the
unpatched source. Fixed: an unreadable fixture now reports `harness-error`
and fails the check, and the CLI stops a run if the unpatched source does not
fire all three canaries.

**P4. `VERSION` is not bumped to 1.1.0-alpha.** The existing structural test
suite pins `VERSION` to exactly `1.0` and requires a `\d+\.\d+` form; the task
names README.md and CHANGELOG.md as the places to state 1.1.0-alpha. The new
package reports `parapet.__version__ == "1.1.0-alpha"` and the CHANGELOG gets
an unreleased 1.1.0-alpha section; `VERSION` stays the version of record of
the last release (1.0).

## 2. Deviations after pre-registration

**D1. Post-prereg plumbing run (2026-11-18 17:05 PST).** After the prereg
commit and before Step 2, I ran the CLI once on C2 with `--forks 2`
(`--workdir ~/parapet-work/dev/cli-dryrun --label dryrun`) to check the
pipeline end to end. With 2 forks every arm is below `min_valid_forks`, so no
cost estimate and no fit was produced. Not evidence; outputs remain in
`~/parapet-work/dev/cli-dryrun/` and its SUMMARY.md is copied to
`evidence/mozilla-2026-11/dev-runs/`. No pre-registered file changed.

**D2. Model server restarted with `OLLAMA_NO_CLOUD=1` (2026-11-18 ~17:17
PST).** Before the first model run, the user-level Ollama server was
restarted with the same settings as in `evidence/INSTALLS.md` plus
`OLLAMA_NO_CLOUD=1`, which turns off Ollama's cloud-model features. Reason:
keep the generator strictly local. Generation settings
(`parapet/settings/generation.yaml`) are unchanged. The first server log is
kept as `ollama-serve-gpu-session1.log`.

**D3. GPU power sampled during generation.** Step 6 (power draw) was run
concurrently with Step 3 generation using `--power-sample` (nvidia-smi every
200 ms), because it costs no extra time. It is listed under Step 6 in
EVIDENCE.md.

**D4. Record-assembly bug fixed; Step 3 records re-rendered (2026-11-18
17:28 PST).** The Step 3 runs computed each candidate's matched reference
(and used it for the "vs matched reference" measurement), but `parapet/cli.py`
did not write the resulting mechanism route into the candidates' hardening
records (`"mechanism": null`). Fixed by moving record writing into
`emit_records()` and adding `python -m parapet rerecord <run dir>`, which
rebuilds `records/` from the saved run outputs, refuses if any patch source
no longer matches the SHA-256 recorded at validation time, and re-runs
nothing. Both Step 3 run directories were re-rendered; the first-written
records are kept unchanged in `records-as-first-written/` next to them. Only
the `mechanism` field (and a new `rendered` field) differs. Same commit: the
dirty-tree check in `git_info()` stripped the first status column, so the
C1 Step 3 manifest lists `M evidence/DEVIATIONS.md` as "outside evidence/";
it was inside `evidence/` (the record keeps the value as written). Step 2
records were not affected (references carry their declared route).

**D5. CPU-only generation timing (2026-11-18 17:28–17:34 PST).** Run on a
second user-level Ollama server on `127.0.0.1:11435` with the GPU hidden
(`CUDA_VISIBLE_DEVICES=-1 GGML_VK_VISIBLE_DEVICES=-1 OLLAMA_VULKAN=0`; the
server log reports `library=cpu`), same model files, same frozen prompt and
generation settings, case C2 only, by calling `parapet.generate.generate()`
directly with the base URL overridden. These five outputs are saved verbatim
under `step3/cpu-only-C2/` for timing; they were not validated or measured
and are not part of the Step 3 candidate set.

**D6. Peak-memory samples were contaminated by the runner's own memory; fixed
and re-measured (found between 17:34 and 17:40 PST on 2026-11-18; fix
committed 17:40:50 PST as `37b153c`).** While
writing up Step 3, every R2 fork in the C1 Step 3 session reported exactly
100,832 KiB, which was also the minimum of the other arms. Diagnosis (reproduced
with `/bin/true`, output in `evidence/mozilla-2026-11/logs/rss_diagnosis.txt`):
`ru_maxrss` returned by the runner's `wait4` includes the parent Python
process's RSS high-water mark, which Linux carries into the child at `exec`.
The pre-registered sample was therefore max(runner high-water, JVM peak). The
runner's high-water mark was about 76 MB in the Step 2 sessions (the
environment capture imports the OpenAI SDK) and about 101 MB in the Step 3
sessions. Any JVM whose true peak was below that was clamped upward. Latency is
unaffected (timed inside the JVM).
Fix: `parapet/measure.py` launches each fork under GNU `time -f %M -o <file>`.
GNU time forks the JVM from its own small process and reports only that
child's peak RSS. The runner refuses to measure without GNU time. The `wait4`
value is still saved per fork as `maxrss_kib_wait4_includes_parent`.
`parapet/settings/measurement.yaml` (`memory_sample`) is updated to say so.
New test: `tests/parapet/test_measure.py`.
Consequence: all v1 peak-memory overheads (Step 2 and Step 3 runs) are
invalid as JVM measurements. They are kept unchanged and reported as v1.
Step 2 and Step 3 were measured again with the fixed runner (v2). Step 3 v2
reuses the saved candidates (`--candidates-from`, no new model call). The v2
sessions also give an independent replicate of every latency estimate.
Both versions are reported in EVIDENCE.md.

Correction note for D6 (added 17:56 PST): the times first written in the D6
heading ("~17:40", "~17:47") were estimates made while writing; the times now
in the heading come from the CPU-only run log and the git commit timestamp.

**D7. v2 measurement sessions (2026-11-18 17:41–17:55 PST).** With the D6 fix
(commit `37b153c`), Step 2 was re-run for C1 and C2 (`step2-v2/`), and Step 3
was re-run for C1 and C2 with `--candidates-from step3/<case>/generation`
(`step3-v2/`): the saved candidates were re-validated and re-measured, no
model was called, and the generation directory (including its power samples)
was copied into the v2 run unchanged. Everything else (cases, budgets,
protocol, decision rule) is as pre-registered. Validation outcomes in v2 are
identical to v1 for every patch.

**D8. Working directory of forked JVMs (noted 2026-11-18 17:58 PST).** In all
Step 2 and Step 3 runs (v1 and v2) the forked JVMs (validation checks and
workload forks) inherited the CLI's working directory, the repository on
`/mnt/d`. Class files, compilation, fork output files and C2's temporary
canary files were on the Linux filesystem (`~/parapet-work/runs`, `/tmp`);
the C1 validation checks read their fixtures from the repository on `/mnt/d`
(validation only, untimed); the timed workload section performs no file I/O.
From Step 4 on, each fork runs with its own fork directory, and each check
with its patch directory, as working directory (`parapet/measure.py`,
`parapet/validate.py`, `parapet/javatools.py`). Steps 2 and 3 are reported as
run.

## 3. Step 4 (after LOCAL-EVIDENCE `fe998326ff39b3ed3bb47a5e4081e3b6e415ad05`)

**D9. Step 4 additions, declared before any L1 run (2026-11-18 ~18:35 PST).**
(a) Case L1 (java-xmlbuilder, CWE-611) is pre-registered in its own
`prereg:` commit, after LOCAL-EVIDENCE: case definition, upstream fix as R1,
hand-written R2 and control, checks, workload, and probes. The checks were
run on the unpatched library and the workload was timed on the unpatched
library only (to set `ops_per_round` to 800) before that commit. R1, R2 and
the control have not been run. (b) Package changes needed for a library case:
multi-file reference patches, compiling the whole library with a patch
applied, dependency jars pinned by SHA-256, library test sources on the
harness sourcepath, `--generation-settings`. C1/C2 behavior is unchanged
(regression-checked by re-rendering a copy of `step3-v2/C2`: identical
records apart from a cosmetic `source_path` prefix). (c) A generation-settings
variant `parapet/settings/generation-longctx.yaml` (32,768-token context,
16,384 `max_tokens`, request timeout 1,200 s, on a second loopback server, port 11436). L1's target
file (~46 KB) cannot fit the frozen settings (8,192 context, 4,096 output
tokens). The frozen settings are run first and are the primary L1 generator
result. The variant is a secondary run, and both are reported.

Correction note for D9 (written 2026-11-18 18:13 PST): the "~18:35 PST" in
the D9 heading was a wrong estimate; D9 was written between 18:05 and 18:12
PST and committed with the L1 pre-registration (`083b7b8`, 18:12:18 PST).

**D10. L1 long-context run killed mid-measurement; re-measured (2026-11-18
18:29–18:36 PST).** The first long-context run (started 18:19:57) completed
generation (18:19:57–18:26:48) and validation, then was killed at 18:29:57 by
my tool's 10-minute limit on foreground commands, after 61 of 140 measurement
forks. Its output directory is kept unchanged as
`step4/L1-gen-longctx-killed/` (generation, validation, partial raw samples,
console log); it has no summary, decision, or records. The saved candidates
were then re-validated and re-measured with `--candidates-from` (no model
call), run in the background, into `step4/L1-gen-longctx/` (18:30:29–18:36:25).
The validation outcomes are identical in the two runs.

**Note on Step 5.** The hosted control was not run because neither
`OPENAI_API_KEY` nor `ANTHROPIC_API_KEY` was set (see EVIDENCE.md section E).
This is the skip the task specifies, recorded here for completeness.
