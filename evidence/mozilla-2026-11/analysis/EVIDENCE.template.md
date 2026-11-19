# PARAPET local slice — evidence package (mozilla-2026-11)

Branch `mozilla/local-slice`, built on tag `v1.0` (`c6a9566`). This package
shows the four-stage workflow — Generate, Validate, Measure, Decide — run per
weakness on two authored Java cases (C1, CWE-502; C2, CWE-611) and one real
library case (L1, java-xmlbuilder, CWE-611). It is not a comparison of
models. Every table is generated from files in this directory by
`analysis/build_doc.py` (templates in `analysis/`). Sections A–C repeat the
content frozen at LOCAL-EVIDENCE (`LOCAL-EVIDENCE.md`, unchanged).

**Read first.** (1) Peak-memory figures exist in two versions: **v1**, from
the pre-registered runner, is invalid as a JVM measurement because it
included the runner's own memory; **v2** is correct (DEVIATIONS D6/D7). L1
was measured only with the corrected runner. (2) Every change after a
pre-registration commit is in `evidence/DEVIATIONS.md` (P1–P4, D1–D14),
reproduced in full in section G. (3) D11–D14 are **post-hoc**: designed
and run after the results were seen (v3 remeasurement, the post-hoc arm
P1, the L1 external-DTD observation, and analysis/wording changes; sections
B.4, C.3, C.8–C.10, D.2, D.4, D.5 and H). They change no case, check,
budget, decision rule, claim level, or existing run directory.

Pre-registration commits: `f9f9e15` (C1, C2, budgets, protocol, prompt,
settings; 2026-11-18 17:05:09 PST) and `083b7b8` (L1; 18:12:18 PST).
Generator-free results were committed before the corresponding model runs
(`5eefe0c` before the first model request at 17:15:45; `2ac5656` before the
first L1 model request at 18:16:06; times from the endpoint logs).

## A. Environment, default generator, installs

| Item | Value |
| --- | --- |
| OS | Ubuntu 26.04 LTS on WSL2, kernel 6.6.114.1-microsoft-standard-WSL2 |
| CPU | Intel Core i9-14900KF, 32 logical CPUs visible to WSL; forks pinned with `taskset -c 2-5` |
| RAM | 31.2 GiB visible to WSL |
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 610.60 (nvidia-smi 610.47.03, CUDA UMD 13.3) |
| JDK | OpenJDK 21.0.13.0.3 (Ubuntu build 21.0.13.0.3+1-1-26.04.1); all Java compiled with `javac --release 17` |
| Python | 3.14.4 (venv under `~/parapet-work/venv`: numpy 2.5.5, openai 2.54.0, PyYAML 6.0.3, pytest 8.4.2) |
| Model server | Ollama 0.40.16, user process on `127.0.0.1:11434` (loopback only), `OLLAMA_CONTEXT_LENGTH=8192`, `OLLAMA_NO_CLOUD=1` from the first model run on (D2) |
| Work directory | compile and measure under `~/parapet-work/runs` (ext4, Linux filesystem); results copied into this directory (see D8 for the JVM working directory) |

**Default generator.** Qwen2.5-Coder-7B-Instruct.

| Property | Value | Source |
| --- | --- | --- |
| Ollama tag | `qwen2.5-coder:7b-instruct-q4_K_M` | `parapet/settings/generation.yaml` |
| Manifest digest | `sha256:dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` | `step3/C1/generation/model.json` (Ollama `/api/tags`) |
| Weights blob (GGUF) | `sha256:60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463`, 4,683,074,048 bytes; hash re-computed locally and matches | Ollama manifest; `sha256sum` |
| Parameter count | 7,615,616,512 (GGUF `general.parameter_count`); model card: "Number of Parameters: 7.61B" | `model.json`; https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct |
| License | Apache-2.0 (model card `license: apache-2.0`; GGUF `general.license`; Ollama license layer is the Apache License 2.0 text) | same |
| Quantization | Q4_K_M (GGUF `file_type` 15), as distributed by Ollama | `model.json` |
| Context | 32,768 trained (GGUF metadata); served with 8,192 | `model.json`; server log |

Generation settings (pre-registered): k = 5, temperature 0.7, top_p 0.95,
seeds 101–105, max_tokens 4096, request timeout 600 s, no retries. Prompt
template `parapet/prompts/harden_v1.txt` (sha256
`d5b3c33c4650e1a53437ad477bd4031896f35b4b33193efb946968f8ed90edbc`); prompt
sha256 C1 `ca4de091367f148432505594779160045f56343829121931948f4c2bf83c07ea`,
C2 `48823d42342e244db8b00af2bff2c0b45a45f62f67066165c71ce0824710bed9`. The
prompt contains the vulnerable source file and the weakness class only
(checked by `tests/parapet/test_prompt_and_generator.py`).

Installs and every network endpoint used for installs and citation checks:
`evidence/INSTALLS.md`. Hugging Face model card fetched once
(`https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/raw/main/README.md`,
2026-11-18 17:14:33 PST) for the parameter count and license.

## B. Workflow without a generator (hand-written patches only)

Budgets: strict = 5% latency / 5% peak memory, lenient = 25% / 25%
(`parapet/budgets/`, sha256 `208491b8306d…` and `fdada931cc93…`). A patch fits
only if the upper end of each 95% interval is at or below the cap. "≈ noise"
marks a point estimate smaller in magnitude than that session's A/A noise
floor (indistinguishable).

### B.1 C1 — CWE-502 (validation, v1 Step 2 session; v2 identical)

{{validation:step2/C1}}

### B.2 C2 — CWE-611 (validation, v1 Step 2 session; v2 identical)

{{validation:step2/C2}}

In both cases the unpatched source fails the checks (all three canaries
fire), R1 and R2 are admissible, and the incomplete control patch blocks the
reproducer but is rejected by both held-out variants.

### B.3 Cost of R1 and R2, A/A noise floor, and decisions — every session

Each session: 20 forked JVMs per arm, arms interleaved, 10 warm-up rounds
discarded, 20 measured rounds. Ratio of medians against that session's
unpatched baseline, 95% percentile bootstrap (10,000 resamples). v1 peak-memory
columns are invalid (D6) and shown only for completeness.

C1 (CWE-502):

{{cross_v3:C1}}

C2 (CWE-611):

{{cross_v3:C2}}

Primary Step 2 tables (v2 session, valid memory):

C1:

{{measurement:step2-v2/C1}}

{{decisions:step2-v2/C1}}

C2:

{{measurement:step2-v2/C2}}

{{decisions:step2-v2/C2}}

What the hand-written patches show:

- C1: R1 (serialization filter) adds a small latency cost in every session;
  R2 (data-only format) is faster than the baseline in every session. Both fit
  both budgets in the four sessions up to LOCAL-EVIDENCE; in the post-hoc v3
  session (D11) R1's latency interval is [+1.97, +5.77], overlapping every
  earlier session, and its upper bound misses the strict cap, so R1 fits the
  strict budget in four of five sessions. The rule recommends R2 in every
  session because its latency upper bound is lowest. R2 rejects every token written by the original
  implementation (6/6 probes); R1 rejects one legacy token shape (1/6). The
  decision rule does not weigh rejected inputs; the records list them for the
  maintainer.
- C2: R1 (reject DOCTYPE) costs about 10% latency in every session and never
  fits the strict budget; it fits the lenient one. R2 (entity resolver) is
  within the noise floor in every session, and fits the strict budget in three
  of four sessions up to LOCAL-EVIDENCE and in the v3 session (four of five). In the v2 Step 2 session its latency upper bound is
  5.08% against a 5.0% cap, so in that session nothing fits the strict budget.
  The strict verdict for a patch whose cost sits inside the noise is therefore
  not stable from session to session.

### B.4 Sessions where strict memory verdicts are not resolvable (D14, post-hoc)

When a session's own A/A peak-memory interval reaches above 5%, two copies of
the same program can differ by more than the strict memory cap. A strict
memory verdict in that session (fits or does not fit, on memory) cannot be
resolved by this measurement. The table covers every session in this package.
The verdicts recorded in each `decision.json` are unchanged; this table
qualifies them.

{{posthoc:memory_resolvability}}

## C. Workflow with the default local generator

Each case was run end to end once (v1, 2026-11-18 17:15–17:26 PST); the saved
candidates were re-validated and re-measured once more without a model call
(v2). Raw outputs are saved verbatim in `step3/<case>/generation/raw/`.

### C.1 Claim levels (per case; levels are not merged)

**What L4 means (D14).** L4 ("admissible") means the patch passes the
registered checks: it compiles, the reproducer and both held-out variants no
longer fire the canary, and the functional tests pass. It does not mean
equal security coverage. Two L4 patches can differ in what they still allow:
which legitimate inputs they now reject (the probe columns), and whether the
parser still reads an external DTD named by the document (section D.4).

{{claims:step3-v2/C1}}

{{claims:step3-v2/C2}}

### C.2 Time and tokens per candidate (GPU, v1 generation run)

C1:

{{generation:step3/C1}}

C2:

{{generation:step3/C2}}

C1's G1 time includes loading the model into GPU memory (first request of the
server session). For C2, seeds 102 and 105 returned byte-identical outputs,
as did seeds 103 and 104, so the five samples contain three distinct outputs.

C1 failures, as observed (no candidate was edited):

- G1: the code block is byte-identical to the original file; it compiles and
  all three canaries fire (L2).
- G2: adds a `resolveClass` override but does not import
  `InvalidClassException` or `ObjectStreamClass`; does not compile (L1).
- G3, G4: move the cast into a type check applied to the object `readObject`
  returns, and drop the `java.util.Base64` import; do not compile (L1).
- G5: builds a custom class around `ObjectInputFilter`; unresolved
  `ObjectInputFilter`, `FilterInfo`, `Status` and an incompatible-type error;
  does not compile (L1).

C2: all five candidates set `disallow-doctype-decl` plus the three external
entity/DTD features, `setXIncludeAware(false)` and
`setExpandEntityReferences(false)`; all are admissible (L4) and reject the
same four DTD probes as R1.

### C.3 Cost of admissible candidates (C2) and excess over matched reference

The matched reference is assigned by the pre-registered rule in
`parapet/cases/C2/case.yaml` (all five set `disallow-doctype-decl` → R1).
Excess over matched reference = candidate against R1, measured in the same
session. (This was labelled "model-induced cost" until D14; the label in the
existing records and run summaries is superseded, and the records are not
rewritten.) R1 sets one feature (`disallow-doctype-decl`) plus
`FEATURE_SECURE_PROCESSING`. The candidates set four features plus two
setters (see C.8), so the excess measures a different configuration. It is
not attributed to the model.

v3 (current runner, valid memory; D11):

{{excess:step3-v3/C2}}

v2 (valid memory):

{{excess:step3-v2/C2}}

v1 (latency valid, memory invalid):

{{excess:step3/C2}}

### C.4 Budget decisions over all admissible patches

C1 (no admissible candidate; the set is R1 and R2), v2:

{{decisions:step3-v2/C1}}

C2 (R1, R2, G1–G5), v2:

{{decisions:step3-v2/C2}}

C2, v1:

{{decisions:step3/C2}}

### C.5 CPU-only generation time (C2, GPU hidden; D5)

{{cpu_only:step3/cpu-only-C2}}

The CPU outputs for seeds 102–105 are byte-identical to the GPU outputs for
the same seeds; seed 101 differs (596 vs 595 completion tokens). These five
outputs were not validated or measured.

### C.6 Endpoint log (model calls)

C1:

{{endpoints:step3/C1}}

C2:

{{endpoints:step3/C2}}

CPU-only run (second local server, port 11435):

{{endpoints:step3/cpu-only-C2}}

v2 runs made no model request. A connection monitor (`ss`, every 2 s,
17:15:39–17:34:33 PST, `logs/ollama_connections_step3.log`) saw only
loopback-to-loopback connections for the Ollama processes. Sampling every 2 s
cannot rule out a shorter-lived connection.

### C.7 GPU board power during generation (Step 6; run concurrently, D3)

C1:

{{power:step3/C1}}

C2:

{{power:step3/C2}}

Whole-board power from `nvidia-smi` every 200 ms; includes anything else
using the GPU (the Windows desktop). Not a per-request energy measurement.

### C.8 setFeature calls, allocation and latency (D14, post-hoc analysis)

Counts are setFeature calls executed per workload operation, excluding
`FEATURE_SECURE_PROCESSING`, read from each patch's source. Allocation and
latency come from the v3 session's summary. This is a description of what
each configuration does; no causal claim is made about which setting costs
what.

C1 (no patch configures an XML parser; the column is 0 throughout):

{{posthoc:feature_table C1 step3-v3/C1}}

C2:

{{posthoc:feature_table C2 step3-v3/C2}}

### C.9 v3 remeasurement with the current runner (D11, post-hoc)

`step3-v3/<case>`: the saved Step 3 candidates and the hand-written patches,
re-validated and re-measured with the current runner. Since D8, fork and check
working directories are on the Linux filesystem. No model call. Validation
outcomes are identical to v1 and v2. The v3 rows are in the cross-session
tables in B.3. Below, per arm: whether the v3 latency interval overlaps the
interval of each earlier session.

C1:

{{posthoc:overlap_table C1}}

C2:

{{posthoc:overlap_table C2}}

v3 budget decisions, C1:

{{decisions:step3-v3/C1}}

v3 budget decisions, C2:

{{decisions:step3-v3/C2}}

### C.10 Post-hoc arm P1 for C2 (D12) — post-hoc, designed after seeing results

P1 is **not a reference fix** and enters no decision table. It is hand-written
from the original C2 source (`posthoc/C2-P1/`). It uses the same four feature
settings and the same two setters as generated candidate G2. The difference:
the configured `DocumentBuilderFactory` is built once at class load and
reused, and each call takes a new `DocumentBuilder` from it under a lock. It
was validated with the registered C2 checks and measured in its own session
with baseline, baseline-AA, R1 and G2 (`posthoc/C2-P1-session/`).

{{posthoc:p1_report}}

## D. Real library case — L1, java-xmlbuilder (CWE-611, CVE-2014-125087)

Library: java-xmlbuilder (https://github.com/jmurty/java-xmlbuilder),
Apache-2.0, pinned at `5d5caa583b14ade1d6713b8e73b58679de50361f`, the parent
of the upstream fix `e6fddca201790abab4f2c274341c0bb8835c3e73` (released in
v1.2). Disclosure: upstream issue #6 (2014-07-22) and CVE-2014-125087 (NVD,
published 2023-02-19, CWE-611; its references list the fix commit). Maintainers: the GitHub
contributors API lists 4 contributors (one with 53 commits, two others with
2 and 1, and dependabot); last push 2020-10-13. Dependents (deps.dev):
version 1.1 has 731 (25 direct), version 1.3 has 69 (11 direct). Raw
responses: `step4/sources/`. Built offline with `javac` against three jars
pinned by SHA-256 (`parapet/cases/L1/fetch_jars.sh`); functional tests are
the library's own 34 JUnit tests at the pinned commit. Only one library was
tried. Case definition: `parapet/cases/L1/` (pre-registered as `083b7b8`
before any patch or generator run on it; D9).

Step 4 started at 18:02 PST (after LOCAL-EVIDENCE) and its last run finished
at {{file:analysis/step4_end_time.txt}} PST, inside the 4-hour limit.

### D.1 Generator-free part (primary evidence; committed as `2ac5656`)

R1 = upstream fix (three files), R2 = OWASP DOM defense (hand-written),
CONTROL = incomplete (hand-written).

{{validation:step4/L1-nogen}}

{{measurement:step4/L1-nogen}}

{{decisions:step4/L1-nogen}}

R1 and R2 were measured again in each generator session (same protocol):

{{cross:L1}}

### D.2 Generator part, frozen settings (primary generator result): prompt truncation

Result: **prompt truncation**. The server cut every prompt to fit the frozen
context, so no candidate could be a patch (L0 5/5, L1 0/5). This shows the
frozen settings do not fit a 46 KB file. It says nothing about the model's
behavior on the full prompt.

Exactly the Step 3 prompt template and settings (8,192-token context, 4,096
`max_tokens`). The full prompt is 10,075 tokens; the server log records
`truncating input prompt limit=4098 prompt=10075` for every request, so the
model saw only the last 4,098 tokens of the file and not the instructions.

{{claims:step4/L1-gen-frozen}}

{{generation:step4/L1-gen-frozen}}

Outputs: G1 a fenced fragment of the file's last methods (no class
declaration); G2–G5 prose descriptions of the class. None is a patch.
G1's time includes loading the model (the server log shows a model load at
18:16:07; the server had been idle past its keep-alive).

### D.3 Generator part, long-context variant (secondary; declared in D9)

Same model, prompt template, temperature, top_p and seeds; context 32,768,
`max_tokens` 16,384, on a second loopback server (port 11436). The first run
was killed by my tool's 10-minute limit during measurement (61 of 140 forks;
its generation and validation outputs are complete and kept in
`step4/L1-gen-longctx-killed/`); the saved candidates were then re-validated
and re-measured with `--candidates-from` (no model call) into
`step4/L1-gen-longctx/`. Validation outcomes are identical in both.

{{claims:step4/L1-gen-longctx}}

{{generation:step4/L1-gen-longctx}}

{{validation:step4/L1-gen-longctx}}

{{measurement:step4/L1-gen-longctx}}

Excess over matched reference (formerly "model-induced cost"; D14). The
pre-registered rule matches G2, G3 and G5 to R2 because each sets
`disallow-doctype-decl`. R2 sets that one feature (plus
`FEATURE_SECURE_PROCESSING`) on the parse factory only. The candidates set
four features and further setters on both the parse and the create factory
(see C.8). So the excess measures a different configuration and is not
attributed to the model:

{{excess:step4/L1-gen-longctx}}

{{decisions:step4/L1-gen-longctx}}

Observed (no candidate was edited): G2, G3 and G5 add
`disallow-doctype-decl` plus `external-general-entities`,
`external-parameter-entities` and `load-external-dtd` set to false to both
the parse and the create factory (G3 and G5 also
`setExpandEntityReferences(false)`). G1 and G4 add no security setting; both
change `isNamespaceAware` from `true` to `false` and reword comments, which
fails `testElementBefore` in both test classes and leaves every canary
firing.

{{file:analysis/step4_narrative.md}}

### D.4 Supplementary observation: is an external DTD named by the document read? (D13, post-hoc)

Not a check and not part of any claim level. The document's DOCTYPE names a
local DTD file that declares an **internal** entity holding a marker string,
and the body uses the entity (`posthoc/L1-dtd-observation/`). If the marker
appears in the parsed document, the parser read the external DTD. One fresh
JVM per patch, same library build layout as validation; no model call.

{{file:posthoc/L1-dtd-observation/results.md}}

### D.5 setFeature calls, allocation and latency for L1 (D14, post-hoc analysis)

Per workload operation the driver calls `XMLBuilder.parse` and
`XMLBuilder.create` once each, so both `parseDocumentImpl` and
`createDocumentImpl` build a factory. Session: long-context run.

{{posthoc:feature_table L1 step4/L1-gen-longctx}}

Endpoint logs (model calls, Step 4):

Frozen settings:

{{endpoints:step4/L1-gen-frozen}}

Long-context variant:

{{endpoints:step4/L1-gen-longctx-killed}}

The re-measurement made no model request. A connection monitor (`ss`, every
2 s, `logs/ollama_connections_step4.log`) covered the Step 4 generation runs
and saw only loopback-to-loopback connections for the Ollama processes.

GPU board power during Step 4 generation (long-context variant):

{{power:step4/L1-gen-longctx}}

## E. Appendix — hosted control (Step 5)

Not run. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` were both unset (checked
at about 16:38 PST on 2026-11-18, when the branch was created, and again at
18:30:58 PST; only presence was checked, no value was read or printed), so the step was skipped as the
task specifies. No hosted endpoint was contacted at any point.
`parapet/generate.py` refuses a non-loopback generator unless
`--allow-hosted-control` is passed (tested in
`tests/parapet/test_prompt_and_generator.py`). Because the local generator
reached L4 on C2, Step 5 was not required as a diagnostic. Consequence: the
attribution question (whether the excess over matched reference and the
failures come from the local generator or from the prompt and cases) is unanswered here.
`controls/README.md` records the same.

## F. Paths and reproduce commands

All paths are relative to `evidence/mozilla-2026-11/`. Every run directory
contains `run.json` (arguments, commit, environment, hashes), `SUMMARY.md`,
`validation/<patch>.json` and `validation/logs/<patch>/` (exact command and
raw output of every check), `measurement/raw_samples.jsonl` (every fork) and
`measurement/summary.json`, `decision.json`, and `records/<patch>.json|.md`
(hardening records). Generator runs add `generation/raw/<G>.txt` (verbatim
model output), `generation/raw/<G>.response.json`,
`generation/extracted/<G>/`, `generation/generation_log.jsonl`,
`generation/endpoint_log.jsonl`, `generation/prompt.txt` and
`generation/gpu_power.csv`.

| Case | Runs (v1 memory invalid, see D6) |
| --- | --- |
| C1 | `step2/C1` (v1), `step2-v2/C1`, `step3/C1` (v1, generation), `step3-v2/C1` |
| C2 | `step2/C2` (v1), `step2-v2/C2`, `step3/C2` (v1, generation), `step3-v2/C2`, `step3/cpu-only-C2` (generation timing only) |
| L1 | `step4/L1-nogen`, `step4/L1-gen-frozen`, `step4/L1-gen-longctx-killed` (generation + validation; measurement incomplete), `step4/L1-gen-longctx` |

Raw-sample SHA-256 for every session is printed in the measurement tables
above and stored in each `measurement/summary.json`; the analysis tables are
rebuilt from these files by `analysis/tables.py`, `analysis/cross_session.py`
and `analysis/build_doc.py`.

One reproduce command per case (from the repository root, Linux, JDK 17+,
GNU `time`, `taskset`, Python 3.10+ with `requirements-dev.txt`; the `openai`
package is needed only to regenerate; re-validates and re-measures the hand-written patches and the saved
candidates without calling a model):

```bash
python -m parapet run --case C1 --candidates-from evidence/mozilla-2026-11/step3/C1/generation --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml
python -m parapet run --case C2 --candidates-from evidence/mozilla-2026-11/step3/C2/generation --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml
parapet/cases/L1/fetch_jars.sh && python -m parapet run --case L1 --candidates-from evidence/mozilla-2026-11/step4/L1-gen-longctx-killed/generation --budget parapet/budgets/strict.parapet.budget.yaml --budget parapet/budgets/lenient.parapet.budget.yaml
```

To regenerate candidates instead, drop `--candidates-from` (needs Ollama with
`qwen2.5-coder:7b-instruct-q4_K_M` on `127.0.0.1:11434`; for L1's variant add
`--generation-settings parapet/settings/generation-longctx.yaml` and a server
on port 11436 with `OLLAMA_CONTEXT_LENGTH=32768`). Sampling may differ.

## G. Every failure and every deviation

Failures observed in the workflow (all reported above; nothing was repaired):

- C1 generator: G1 returned the file unchanged (L2, all canaries fire);
  G2–G5 do not compile (L1): missing imports and unresolved
  `ObjectInputFilter` types.
- C2 generator: all five admissible, all five fail both budgets on latency.
- L1 frozen settings: prompt truncation by the server (10,075 → 4,098 tokens);
  0/5 parseable.
- L1 long-context variant: G1 and G4 compile but change namespace handling,
  fail 2/34 upstream tests, and leave all canaries firing (L2).
- Budget outcomes where no admissible patch fits: C2 strict in the v2 Step 2
  session; L1 strict in every session. C1 R1 misses the strict cap in the
  post-hoc v3 session (D11).

Failures in my own work:

- Harness defect before pre-registration (unreadable fixture counted as a
  pass; P3).
- Runner defect: peak memory included the runner's own RSS high-water mark;
  every v1 memory figure is invalid (D6); re-measured (D7).
- Record defect: candidate records first written without a mechanism route
  (D4).
- JVM working directory on `/mnt/d` during Steps 2–3 (D8).
- The L1 long-context run killed by my tool's time limit mid-measurement
  (D.3); re-measured from saved candidates.
- Times written by estimate in D6 and D9 headings, corrected in place with
  notes.
- Two `kill` pattern matches that ended my own calling shell (no other
  process affected).

`evidence/DEVIATIONS.md` in full:

{{file_demoted:../DEVIATIONS.md}}

## H. What these results do not show

- **Architecture-level and resource-contention costs.** Every number is a
  single-threaded workload in one JVM pinned to four vCPUs on an otherwise
  quiet machine. Nothing here measures contention, cache or memory-bandwidth
  interference, or costs that appear only across services.
- **Behavior under concurrent load.** No multi-threaded or multi-request
  workload was run.
- **Downstream product cost.** Inputs a patch now rejects are listed (for
  example, C1 R2 rejects every token the original wrote; L1 R2 rejects every
  document with a DOCTYPE), but their cost to users, migrations, or the 731 /
  69 deps.dev dependents of java-xmlbuilder is not measured. The decision
  rule does not weigh rejected inputs at all.
- **Weakness classes not tested.** Only CWE-502 and CWE-611, only Java, two
  authored cases and one library. No other CWE, language, or library.
- **Any comparison of model sizes.** One local model was used. Nothing here
  compares models or model sizes, and the hosted control (which would only
  have addressed attribution) was not run.
- **Exploitability beyond the canaries.** "Fires" means a canary flag was
  set (C1) or a marker file's content was reflected (C2, L1). Out-of-band
  effects are not detected: a fetch of an attacker-named resource that
  reflects no content would not make any canary fire. Observed directly in
  the supplementary observation (D.4, D13): with L1's R1 (the upstream fix),
  as with the unpatched library and the control, the parser reads an external
  DTD named by the document. A marker defined as an internal entity in that
  DTD appears in the parsed document. R2 and the admissible generated
  candidates G2, G3 and G5 reject that document (DOCTYPE disallowed). The
  registered checks do not test DTD loading by itself, so R1 is L4 while
  still reading external DTDs. (The earlier wording inferred this from R1
  accepting the benign external-DTD probe; acceptance alone did not show
  that the DTD was read.) No real exploit chain was used.
- **Stability of budget verdicts.** Each session has its own A/A noise
  floor, and intervals do not cover session-to-session variation. A patch
  whose cost sits inside the noise can fit a 5% cap in one session and miss
  it in another (C2 R2: four of five sessions; C1 R1: four of five, missing
  only in v3). "Indistinguishable" is
  judged on the point estimate against the noise floor, as pre-registered.
- **Memory.** Peak RSS of a JVM run with `-XX:+UseSerialGC -Xms64m
  -Xmx512m`; it reflects heap sizing as much as live data. v1 memory figures
  are invalid (D6). Allocation per operation is reported but not budgeted.
- **Other JDKs, parsers, and machines.** OpenJDK 21 on WSL2 on one host. The
  costs of parser features (for example, setting external-entity features
  versus rejecting DOCTYPE) may differ on other JDKs or parser
  implementations; no causal explanation of the observed costs is offered.
- **Generation at scale.** k = 5, one generation run per case and setting.
  The whole-file prompt does not fit a 1,347-line file under the frozen
  settings (L1). Seeds did not give five distinct outputs (C2: three).
- **Energy.** GPU power is whole-board power sampled every 200 ms, including
  the desktop; it is not a per-request energy measurement. CPU energy was
  not measured.
- **Components not exercised.** CoQuIR, LUNA, PrivAuditor and Metior were
  not used. Choosing fixes across several weaknesses within one budget is
  planned, not built.

## I. Test results

{{file:analysis/final_tests.md}}

## J. One line per case

{{file:analysis/one_line_per_case.md}}

---

Branch: `mozilla/local-slice`
LOCAL-EVIDENCE: `fe998326ff39b3ed3bb47a5e4081e3b6e415ad05`
Final: {{file:analysis/final_hash.txt}}
