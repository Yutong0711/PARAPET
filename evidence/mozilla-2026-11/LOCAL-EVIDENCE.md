# LOCAL-EVIDENCE — Steps 0–3, branch `mozilla/local-slice`

This file freezes the local evidence (Steps 0–3) at the commit recorded as
LOCAL-EVIDENCE in `EVIDENCE.md`. Later steps do not alter it. Every table
below is generated from files in this directory by
`analysis/build_doc.py` from `analysis/LOCAL-EVIDENCE.template.md`.

Timeline (PST, 2026-11-18): pre-registration commit `f9f9e15` at 17:05:09;
Step 2 results committed as `5eefe0c` at 17:14:20; first model request at
17:15:45 (Step 3, C1). Every change after pre-registration is in
`../DEVIATIONS.md` (D1–D8), and the disclosures from before it are listed there as P1–P4.

**Read first: two measurement versions.** The pre-registered runner took
peak memory from its own `wait4`, which on Linux includes the runner's own RSS
high-water mark (DEVIATIONS D6). Every **v1** peak-memory figure is therefore
invalid as a JVM measurement; v1 latency is valid. The runner was fixed and
every measurement session was repeated (**v2**). Both versions are reported.
Validation outcomes are identical in v1 and v2.

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
`../INSTALLS.md`. Hugging Face model card fetched once
(`https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct/raw/main/README.md`,
2026-11-18 17:14:33 PST) for the parameter count and license.

## B. Workflow without a generator (hand-written patches only)

Budgets: strict = 5% latency / 5% peak memory, lenient = 25% / 25%
(`parapet/budgets/`, sha256 `208491b8306d…` and `fdada931cc93…`). A patch fits
only if the upper end of each 95% interval is at or below the cap. "≈ noise"
marks a point estimate smaller in magnitude than that session's A/A noise
floor (indistinguishable).

### B.1 C1 — CWE-502 (validation, v1 Step 2 session; v2 identical)

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (GadgetA.readObject) | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: probe_legacy_linkedlist.b64 |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 6/6: probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |

### B.2 C2 — CWE-611 (validation, v1 Step 2 session; v2 identical)

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (result:config.name) | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: external_dtd_benign_local |

In both cases the unpatched source fails the checks (all three canaries
fire), R1 and R2 are admissible, and the incomplete control patch blocks the
reproducer but is rejected by both held-out variants.

### B.3 Cost of R1 and R2, A/A noise floor, and decisions — every session

Each session: 20 forked JVMs per arm, arms interleaved, 10 warm-up rounds
discarded, 20 measured rounds. Ratio of medians against that session's
unpatched baseline, 95% percentile bootstrap (10,000 resamples). v1 peak-memory
columns are invalid (D6) and shown only for completeness.

C1 (CWE-502):

| Session | Arm | Latency overhead [95% CI] | Peak-memory overhead [95% CI] | A/A noise floor (lat / mem) | Strict | Lenient |
| --- | --- | --- | --- | --- | --- | --- |
| v1 Step 2 | R1 | +2.73% [+0.86, +4.24] | -1.52% [-4.32, +1.17] ≈ noise | 1.23% / 1.81% | fits | fits |
| v1 Step 2 | R2 | -62.94% [-63.55, -62.13] | -26.64% [-27.41, -25.44] | 1.23% / 1.81% | fits (recommended) | fits (recommended) |
| v1 Step 3 | R1 | +1.73% [+0.51, +3.47] | -1.93% [-2.96, +0.50] ≈ noise | 1.60% / 2.33% | fits | fits |
| v1 Step 3 | R2 | -62.58% [-63.61, -61.78] | -2.59% [-3.22, -1.31] | 1.60% / 2.33% | fits (recommended) | fits (recommended) |
| v2 Step 2 | R1 | +2.54% [+0.74, +3.78] | -1.44% [-4.04, +0.30] ≈ noise | 2.27% / 1.91% | fits | fits |
| v2 Step 2 | R2 | -63.45% [-64.02, -63.09] | -26.84% [-27.31, -25.09] | 2.27% / 1.91% | fits (recommended) | fits (recommended) |
| v2 Step 3 | R1 | +3.26% [+2.21, +4.47] | -1.53% [-4.40, -0.06] ≈ noise | 3.03% / 2.08% | fits | fits |
| v2 Step 3 | R2 | -63.09% [-63.60, -62.39] | -26.36% [-27.97, -25.17] | 3.03% / 2.08% | fits (recommended) | fits (recommended) |

C2 (CWE-611):

| Session | Arm | Latency overhead [95% CI] | Peak-memory overhead [95% CI] | A/A noise floor (lat / mem) | Strict | Lenient |
| --- | --- | --- | --- | --- | --- | --- |
| v1 Step 2 | R1 | +9.98% [+4.25, +11.96] | +2.47% [-1.81, +5.09] ≈ noise | 4.93% / 3.65% | no | fits |
| v1 Step 2 | R2 | +1.30% [-3.75, +3.17] ≈ noise | -2.07% [-4.33, +3.36] ≈ noise | 4.93% / 3.65% | fits (recommended) | fits (recommended) |
| v1 Step 3 | R1 | +10.86% [+8.16, +14.52] | +0.63% [-3.50, +3.02] ≈ noise | 4.32% / 3.69% | no | fits |
| v1 Step 3 | R2 | +3.05% [+0.93, +4.84] ≈ noise | +0.10% [-2.96, +3.78] ≈ noise | 4.32% / 3.69% | fits (recommended) | fits (recommended) |
| v1 Step 3 | G1 | +34.36% [+31.45, +39.84] | -1.75% [-5.43, +0.35] ≈ noise | 4.32% / 3.69% | no | no |
| v1 Step 3 | G2 | +36.86% [+32.93, +41.07] | +0.31% [-4.05, +2.73] ≈ noise | 4.32% / 3.69% | no | no |
| v1 Step 3 | G3 | +35.19% [+32.12, +39.89] | -1.85% [-5.15, -0.72] ≈ noise | 4.32% / 3.69% | no | no |
| v1 Step 3 | G4 | +34.75% [+31.60, +37.73] | -2.34% [-5.55, -1.03] ≈ noise | 4.32% / 3.69% | no | no |
| v1 Step 3 | G5 | +33.74% [+30.64, +35.75] | -0.82% [-5.28, +2.83] ≈ noise | 4.32% / 3.69% | no | no |
| v2 Step 2 | R1 | +9.62% [+7.06, +11.48] | +0.54% [-2.74, +4.45] ≈ noise | 2.72% / 3.55% | no | fits |
| v2 Step 2 | R2 | +2.00% [-0.64, +5.08] ≈ noise | -0.40% [-2.18, +4.68] ≈ noise | 2.72% / 3.55% | no | fits (recommended) |
| v2 Step 3 | R1 | +11.01% [+8.28, +15.47] | +3.83% [+0.30, +5.52] ≈ noise | 2.99% / 4.83% | no | fits |
| v2 Step 3 | R2 | +2.34% [+0.39, +4.68] ≈ noise | +2.21% [-2.15, +4.42] ≈ noise | 2.99% / 4.83% | fits (recommended) | fits (recommended) |
| v2 Step 3 | G1 | +35.22% [+32.67, +38.26] | -0.78% [-3.80, +1.52] ≈ noise | 2.99% / 4.83% | no | no |
| v2 Step 3 | G2 | +36.46% [+33.07, +39.68] | -0.13% [-3.67, +4.02] ≈ noise | 2.99% / 4.83% | no | no |
| v2 Step 3 | G3 | +35.92% [+33.58, +41.09] | -0.43% [-4.21, +2.03] ≈ noise | 2.99% / 4.83% | no | no |
| v2 Step 3 | G4 | +35.49% [+31.89, +37.61] | +2.17% [-3.87, +4.77] ≈ noise | 2.99% / 4.83% | no | no |
| v2 Step 3 | G5 | +34.81% [+31.29, +38.92] | -0.65% [-4.44, +2.71] ≈ noise | 2.99% / 4.83% | no | no |

Primary Step 2 tables (v2 session, valid memory):

C1:

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `a1c147bdf667a3679670b6481da7e6764d43bfb4e552180a6338a9eb979719be`.

A/A noise floor: latency **2.27%**, peak memory **1.91%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 12683.4 | 104156 | 39793 | — | — |
| baseline-AA | 20/20 | 12585.4 | 103264 | 39809 | -0.77% [-2.27, +1.01] ≈ noise | -0.86% [-1.91, +0.48] ≈ noise |
| R1 | 20/20 | 13005.5 | 102658 | 41517 | +2.54% [+0.74, +3.78] | -1.44% [-4.04, +0.30] ≈ noise |
| R2 | 20/20 | 4635.9 | 76198 | 27277 | -63.45% [-64.02, -63.09] | -26.84% [-27.31, -25.09] |

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2, R1 | R2 | — |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

C2:

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `4866dacfa3f1cd52ac8c20c978630f20b7caef291910699eadac08bfcecac798`.

A/A noise floor: latency **2.72%**, peak memory **3.55%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 63067.5 | 111730 | 169645 | — | — |
| baseline-AA | 20/20 | 63552.4 | 110992 | 169637 | +0.77% [-2.05, +2.72] ≈ noise | -0.66% [-3.55, +2.68] ≈ noise |
| R1 | 20/20 | 69131.5 | 112334 | 191081 | +9.62% [+7.06, +11.48] | +0.54% [-2.74, +4.45] ≈ noise |
| R2 | 20/20 | 64329.2 | 111280 | 169977 | +2.00% [-0.64, +5.08] ≈ noise | -0.40% [-2.18, +4.68] ≈ noise |

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | none | none | R1: latency overhead upper bound 11.48% > cap 5.0%; R2: latency overhead upper bound 5.08% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

What the hand-written patches show:

- C1: R1 (serialization filter) adds a small latency cost in every session;
  R2 (data-only format) is faster than the baseline in every session. Both fit
  both budgets in every session; the rule recommends R2 because its latency
  upper bound is lowest. R2 rejects every token written by the original
  implementation (6/6 probes); R1 rejects one legacy token shape (1/6). The
  decision rule does not weigh rejected inputs; the records list them for the
  maintainer.
- C2: R1 (reject DOCTYPE) costs about 10% latency in every session and never
  fits the strict budget; it fits the lenient one. R2 (entity resolver) is
  within the noise floor in every session, and fits the strict budget in three
  of four sessions. In the v2 Step 2 session its latency upper bound is
  5.08% against a 5.0% cap, so in that session nothing fits the strict budget.
  The strict verdict for a patch whose cost sits inside the noise is therefore
  not stable from session to session.

## C. Workflow with the default local generator

Each case was run end to end once (v1, 2026-11-18 17:15–17:26 PST); the saved
candidates were re-validated and re-measured once more without a model call
(v2). Raw outputs are saved verbatim in `step3/<case>/generation/raw/`.

### C.1 Claim levels (per case; levels are not merged)

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | 5/5 | 5/5 | 1/5 | 0/5 | 0/5 | 0/5 | 0/5 |

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C2 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 0/5 |

### C.2 Time and tokens per candidate (GPU, v1 generation run)

C1:

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 38.55 | 845 | 710 | stop | `0e9394a2da68cd7b…` | L2 |
| G2 | 102 | 6.33 | 845 | 902 | stop | `c8f9cdef50dbbf1d…` | L1 |
| G3 | 103 | 6.93 | 845 | 975 | stop | `632638d77cf93dd1…` | L1 |
| G4 | 104 | 6.25 | 845 | 849 | stop | `4e6ba5bed9b40c30…` | L1 |
| G5 | 105 | 7.46 | 845 | 1058 | stop | `693cd06806f6f993…` | L1 |

C2:

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 4.43 | 627 | 595 | stop | `514b0502cec45b6d…` | L4 |
| G2 | 102 | 4.04 | 627 | 587 | stop | `b298ef7d62e80430…` | L4 |
| G3 | 103 | 4.06 | 627 | 587 | stop | `d73163d4d23adb2d…` | L4 |
| G4 | 104 | 4.04 | 627 | 587 | stop | `d73163d4d23adb2d…` | L4 |
| G5 | 105 | 4.08 | 627 | 587 | stop | `b298ef7d62e80430…` | L4 |

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

### C.3 Cost of admissible candidates (C2) and model-induced cost

The matched reference is assigned by the pre-registered rule in
`parapet/cases/C2/case.yaml` (all five set `disallow-doctype-decl` → R1).
Model-induced cost = candidate against R1, measured in the same session.

v2 (valid memory):

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +35.22% [+32.67, +38.26] | +21.81% [+17.08, +25.36] | -4.44% [-6.96, -1.33] ≈ noise |
| G2 | R1 | +36.46% [+33.07, +39.68] | +22.92% [+17.88, +26.59] | -3.82% [-6.93, +0.83] ≈ noise |
| G3 | R1 | +35.92% [+33.58, +41.09] | +22.44% [+17.72, +27.52] | -4.11% [-7.25, -0.73] ≈ noise |
| G4 | R1 | +35.49% [+31.89, +37.61] | +22.05% [+17.07, +24.85] | -1.60% [-7.29, +1.89] ≈ noise |
| G5 | R1 | +34.81% [+31.29, +38.92] | +21.44% [+16.18, +25.50] | -4.31% [-8.09, +0.06] ≈ noise |

v1 (latency valid, memory invalid):

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +34.36% [+31.45, +39.84] | +21.19% [+17.50, +26.25] | -2.36% [-5.51, +1.43] ≈ noise |
| G2 | R1 | +36.86% [+32.93, +41.07] | +23.45% [+18.93, +27.34] | -0.31% [-4.35, +3.55] ≈ noise |
| G3 | R1 | +35.19% [+32.12, +39.89] | +21.94% [+18.14, +26.36] | -2.46% [-5.45, +0.84] ≈ noise |
| G4 | R1 | +34.75% [+31.60, +37.73] | +21.55% [+17.61, +24.52] | -2.94% [-5.60, +0.35] ≈ noise |
| G5 | R1 | +33.74% [+30.64, +35.75] | +20.64% [+16.64, +22.82] | -1.44% [-5.15, +3.50] ≈ noise |

### C.4 Budget decisions over all admissible patches

C1 (no admissible candidate; the set is R1 and R2), v2:

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2, R1 | R2 | — |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

C2 (R1, R2, G1–G5), v2:

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G1, G2, G3, G4, G5 | R2 | R2 | R1: latency overhead upper bound 15.47% > cap 5.0%, peak-memory overhead upper bound 5.52% > cap 5.0%; G1: latency overhead upper bound 38.26% > cap 5.0%; G2: latency overhead upper bound 39.68% > cap 5.0%; G3: latency overhead upper bound 41.09% > cap 5.0%; G4: latency overhead upper bound 37.61% > cap 5.0%; G5: latency overhead upper bound 38.92% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G1, G2, G3, G4, G5 | R2, R1 | R2 | G1: latency overhead upper bound 38.26% > cap 25.0%; G2: latency overhead upper bound 39.68% > cap 25.0%; G3: latency overhead upper bound 41.09% > cap 25.0%; G4: latency overhead upper bound 37.61% > cap 25.0%; G5: latency overhead upper bound 38.92% > cap 25.0% |

C2, v1:

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G1, G2, G3, G4, G5 | R2 | R2 | R1: latency overhead upper bound 14.52% > cap 5.0%; G1: latency overhead upper bound 39.84% > cap 5.0%; G2: latency overhead upper bound 41.07% > cap 5.0%; G3: latency overhead upper bound 39.89% > cap 5.0%; G4: latency overhead upper bound 37.73% > cap 5.0%; G5: latency overhead upper bound 35.75% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G1, G2, G3, G4, G5 | R2, R1 | R2 | G1: latency overhead upper bound 39.84% > cap 25.0%; G2: latency overhead upper bound 41.07% > cap 25.0%; G3: latency overhead upper bound 39.89% > cap 25.0%; G4: latency overhead upper bound 37.73% > cap 25.0%; G5: latency overhead upper bound 35.75% > cap 25.0% |

### C.5 CPU-only generation time (C2, GPU hidden; D5)

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Completion tokens / s | Raw output sha256 | L1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 68.75 | 627 | 596 | 8.7 | `7b611b9273c5b16a…` | True |
| G2 | 102 | 56.37 | 627 | 587 | 10.4 | `b298ef7d62e80430…` | True |
| G3 | 103 | 55.72 | 627 | 587 | 10.5 | `d73163d4d23adb2d…` | True |
| G4 | 104 | 56.77 | 627 | 587 | 10.3 | `d73163d4d23adb2d…` | True |
| G5 | 105 | 53.63 | 627 | 587 | 10.9 | `b298ef7d62e80430…` | True |

Total wall-clock for k = 5: 291.2 s. Source: `step3/cpu-only-C2/generation/generation_log.jsonl`.

The CPU outputs for seeds 102–105 are byte-identical to the GPU outputs for
the same seeds; seed 101 differs (596 vs 595 completion tokens). These five
outputs were not validated or measured.

### C.6 Endpoint log (model calls)

C1:

| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-18T17:15:45-0800 | GET | `http://127.0.0.1:11434/api/version` | model metadata |  | ok | 0.006 |
| 2026-11-18T17:15:45-0800 | GET | `http://127.0.0.1:11434/api/tags` | model metadata |  | ok | 0.001 |
| 2026-11-18T17:15:45-0800 | POST | `http://127.0.0.1:11434/api/show` | model metadata |  | ok | 0.02 |
| 2026-11-18T17:16:24-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 101 | ok | 38.549 |
| 2026-11-18T17:16:30-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 102 | ok | 6.334 |
| 2026-11-18T17:16:37-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 103 | ok | 6.933 |
| 2026-11-18T17:16:43-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 104 | ok | 6.248 |
| 2026-11-18T17:16:51-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 105 | ok | 7.462 |

C2:

| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-18T17:20:12-0800 | GET | `http://127.0.0.1:11434/api/version` | model metadata |  | ok | 0.005 |
| 2026-11-18T17:20:12-0800 | GET | `http://127.0.0.1:11434/api/tags` | model metadata |  | ok | 0.001 |
| 2026-11-18T17:20:12-0800 | POST | `http://127.0.0.1:11434/api/show` | model metadata |  | ok | 0.001 |
| 2026-11-18T17:20:17-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 101 | ok | 4.434 |
| 2026-11-18T17:20:21-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 102 | ok | 4.042 |
| 2026-11-18T17:20:25-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 103 | ok | 4.058 |
| 2026-11-18T17:20:29-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 104 | ok | 4.044 |
| 2026-11-18T17:20:33-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 105 | ok | 4.077 |

CPU-only run (second local server, port 11435):

| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-18T17:28:55-0800 | GET | `http://127.0.0.1:11435/api/version` | model metadata |  | ok | 0.005 |
| 2026-11-18T17:28:55-0800 | GET | `http://127.0.0.1:11435/api/tags` | model metadata |  | ok | 0.001 |
| 2026-11-18T17:28:55-0800 | POST | `http://127.0.0.1:11435/api/show` | model metadata |  | ok | 0.021 |
| 2026-11-18T17:30:04-0800 | POST | `http://127.0.0.1:11435/v1/chat/completions` | candidate generation | 101 | ok | 68.748 |
| 2026-11-18T17:31:01-0800 | POST | `http://127.0.0.1:11435/v1/chat/completions` | candidate generation | 102 | ok | 56.367 |
| 2026-11-18T17:31:56-0800 | POST | `http://127.0.0.1:11435/v1/chat/completions` | candidate generation | 103 | ok | 55.721 |
| 2026-11-18T17:32:53-0800 | POST | `http://127.0.0.1:11435/v1/chat/completions` | candidate generation | 104 | ok | 56.769 |
| 2026-11-18T17:33:47-0800 | POST | `http://127.0.0.1:11435/v1/chat/completions` | candidate generation | 105 | ok | 53.627 |

v2 runs made no model request. A connection monitor (`ss`, every 2 s,
17:15:39–17:34:33 PST, `logs/ollama_connections_step3.log`) saw only
loopback-to-loopback connections for the Ollama processes. Sampling every 2 s
cannot rule out a shorter-lived connection.

### C.7 GPU board power during generation (Step 6; run concurrently, D3)

C1:

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 190 | 68.6 | 313.7 | 2597 |
| G2 | 32 | 310.8 | 313.8 | 1938 |
| G3 | 34 | 310.1 | 318.5 | 2061 |
| G4 | 30 | 304.9 | 318.2 | 1837 |
| G5 | 37 | 315.1 | 318.6 | 2286 |

First samples before the first request (board idle plus desktop): 22.0, 22.1, 22.8 W. 323 samples at 200 ms from `generation/gpu_power.csv`.

C2:

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 22 | 242.1 | 306.9 | 1039 |
| G2 | 20 | 305.5 | 307.7 | 1168 |
| G3 | 21 | 306.2 | 307.9 | 1232 |
| G4 | 20 | 307.4 | 309.9 | 1176 |
| G5 | 20 | 307.1 | 308.3 | 1174 |

First samples before the first request (board idle plus desktop): 21.1, 21.7, 44.4 W. 103 samples at 200 ms from `generation/gpu_power.csv`.

Whole-board power from `nvidia-smi` every 200 ms; includes anything else
using the GPU (the Windows desktop). Not a per-request energy measurement.

## Failures and deviations up to LOCAL-EVIDENCE

- Model-induced failures: C1 G1 unchanged output (L2); C1 G2–G5 compile
  errors (L1). C2: none below L4; all five fail both budgets on latency.
- Harness defect found and fixed before pre-registration (P3).
- Runner defect: peak memory included the runner's memory (D6); all v1
  memory figures are invalid; re-measured as v2 (D7).
- Record defect: candidate records first written without the mechanism route
  (D4); re-rendered from saved outputs, first-written copies kept.
- JVM working directory on `/mnt/d` during Steps 2–3 (D8).
- Two mistaken `kill` commands in my own shell (the pattern matched the
  calling shell) ended that shell; only my own processes were affected.
- See `../DEVIATIONS.md` for P1–P4 and D1–D8 in full.

## Tests at LOCAL-EVIDENCE

Command: `PYTHON=~/parapet-work/venv/bin/python ./scripts/run_tests.sh` (run 2026-11-18 ~18:03 PST at commit `03c9ad6`).
Result: 444 passed (241 + 8 + 195), 0 failed, 0 skipped; 225 deselections are the marker split between suites.

```text
=== Component functional and Python runtime smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/more_than_just_functional tests/parapet -m not jvm
====================== 241 passed, 8 deselected in 4.41s =======================
=== Java/JVM end-to-end smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/parapet -m jvm
====================== 8 passed, 217 deselected in 26.87s ======================
=== Repository and website structural checks ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/repository tests/website
============================= 195 passed in 3.71s ==============================
All selected PARAPET checks passed.
```

## One line per case (Step 3)

- C1 (CWE-502): the default local generator did not reach L4 (best: L2, 1/5; 4/5 stopped at L1); no generated patch fits either budget; R1 and R2 fit both budgets in every session.
- C2 (CWE-611): the default local generator reached L4 (5/5); no generated patch fits the strict or the lenient budget (latency upper bounds 35.75–41.09% across v1 and v2); R2 fits the strict budget in three of four sessions, and R1 and R2 fit the lenient budget in every session.
