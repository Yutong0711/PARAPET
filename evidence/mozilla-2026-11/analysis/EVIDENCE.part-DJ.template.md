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
