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
| v3 Step 3 | R1 | +4.37% [+1.97, +5.77] | -1.57% [-4.12, -0.14] ≈ noise | 3.99% / 1.75% | no | fits |
| v3 Step 3 | R2 | -63.11% [-63.87, -62.54] | -25.99% [-26.62, -24.64] | 3.99% / 1.75% | fits (recommended) | fits (recommended) |

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
| v3 Step 3 | R1 | +9.52% [+8.43, +11.29] | -1.54% [-2.91, +1.03] ≈ noise | 3.23% / 4.56% | no | fits |
| v3 Step 3 | R2 | +1.45% [+0.67, +3.54] ≈ noise | +0.61% [-1.10, +4.20] ≈ noise | 3.23% / 4.56% | fits (recommended) | fits (recommended) |
| v3 Step 3 | G1 | +33.03% [+31.42, +35.07] | -3.45% [-5.85, +0.31] ≈ noise | 3.23% / 4.56% | no | no |
| v3 Step 3 | G2 | +33.46% [+31.37, +36.25] | -1.69% [-3.79, +3.64] ≈ noise | 3.23% / 4.56% | no | no |
| v3 Step 3 | G3 | +33.81% [+32.12, +36.39] | -2.97% [-5.21, +0.91] ≈ noise | 3.23% / 4.56% | no | no |
| v3 Step 3 | G4 | +33.94% [+32.53, +36.10] | -2.37% [-4.01, +0.61] ≈ noise | 3.23% / 4.56% | no | no |
| v3 Step 3 | G5 | +31.95% [+31.07, +34.23] | -2.03% [-4.00, +3.69] ≈ noise | 3.23% / 4.56% | no | no |

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

| Session | A/A peak-memory overhead [95% CI] | Upper bound > 5%? | Strict memory verdicts in this session |
| --- | --- | --- | --- |
| C1 v1 Step 2 | +0.43% [-1.02, +1.81] ≈ noise | no | v1 memory invalid (D6) |
| C1 v1 Step 3 | +0.64% [-0.56, +2.33] ≈ noise | no | v1 memory invalid (D6) |
| C1 v2 Step 2 | -0.86% [-1.91, +0.48] ≈ noise | no | resolvable |
| C1 v2 Step 3 | -0.59% [-2.08, +0.46] ≈ noise | no | resolvable |
| C1 v3 Step 3 | -0.15% [-1.75, +1.29] ≈ noise | no | resolvable |
| C2 v1 Step 2 | +0.22% [-2.76, +3.65] ≈ noise | no | v1 memory invalid (D6) |
| C2 v1 Step 3 | +0.63% [-3.69, +2.16] ≈ noise | no | v1 memory invalid (D6) |
| C2 v2 Step 2 | -0.66% [-3.55, +2.68] ≈ noise | no | resolvable |
| C2 v2 Step 3 | +0.84% [-1.67, +4.83] ≈ noise | no | resolvable |
| C2 v3 Step 3 | +0.29% [-2.04, +4.56] ≈ noise | no | resolvable |
| L1 no generator | -1.16% [-5.86, +5.47] ≈ noise | yes | **not resolvable** for R1, R2 |
| L1 frozen-settings run | +0.25% [-3.89, +4.40] ≈ noise | no | resolvable |
| L1 long-context run | +2.22% [-3.50, +6.22] ≈ noise | yes | **not resolvable** for R1, R2, G2, G3, G5 |
| C2 post-hoc P1 session | +1.07% [-1.59, +3.21] ≈ noise | no | resolvable |

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

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (excess over matched reference) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +33.03% [+31.42, +35.07] | +21.47% [+19.79, +22.84] | -1.95% [-4.34, +0.88] ≈ noise |
| G2 | R1 | +33.46% [+31.37, +36.25] | +21.86% [+19.72, +23.85] | -0.16% [-2.25, +4.10] ≈ noise |
| G3 | R1 | +33.81% [+32.12, +36.39] | +22.19% [+20.38, +24.17] | -1.46% [-3.66, +1.41] ≈ noise |
| G4 | R1 | +33.94% [+32.53, +36.10] | +22.30% [+20.72, +23.80] | -0.85% [-2.44, +1.11] ≈ noise |
| G5 | R1 | +31.95% [+31.07, +34.23] | +20.48% [+19.32, +22.27] | -0.50% [-2.56, +4.56] ≈ noise |

v2 (valid memory):

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (excess over matched reference) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +35.22% [+32.67, +38.26] | +21.81% [+17.08, +25.36] | -4.44% [-6.96, -1.33] ≈ noise |
| G2 | R1 | +36.46% [+33.07, +39.68] | +22.92% [+17.88, +26.59] | -3.82% [-6.93, +0.83] ≈ noise |
| G3 | R1 | +35.92% [+33.58, +41.09] | +22.44% [+17.72, +27.52] | -4.11% [-7.25, -0.73] ≈ noise |
| G4 | R1 | +35.49% [+31.89, +37.61] | +22.05% [+17.07, +24.85] | -1.60% [-7.29, +1.89] ≈ noise |
| G5 | R1 | +34.81% [+31.29, +38.92] | +21.44% [+16.18, +25.50] | -4.31% [-8.09, +0.06] ≈ noise |

v1 (latency valid, memory invalid):

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (excess over matched reference) | Peak memory vs matched reference [95% CI] |
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

### C.8 setFeature calls, allocation and latency (D14, post-hoc analysis)

Counts are setFeature calls executed per workload operation, excluding
`FEATURE_SECURE_PROCESSING`, read from each patch's source. Allocation and
latency come from the v3 session's summary. This is a description of what
each configuration does; no causal claim is made about which setting costs
what.

C1 (no patch configures an XML parser; the column is 0 throughout):

| Patch | setFeature calls per workload operation (excl. FEATURE_SECURE_PROCESSING) | Median allocation per operation (bytes) | Latency overhead vs baseline [95% CI] | How the count was derived |
| --- | --- | --- | --- | --- |
| baseline | 0 | 39773 | — | no setFeature call |
| R1 | 0 | 41549 | +4.37% [+1.97, +5.77] | no setFeature call |
| R2 | 0 | 27277 | -63.11% [-63.87, -62.54] | no setFeature call |

Session: `step3-v3/C1` (allocation and latency from `measurement/summary.json`).

C2:

| Patch | setFeature calls per workload operation (excl. FEATURE_SECURE_PROCESSING) | Median allocation per operation (bytes) | Latency overhead vs baseline [95% CI] | How the count was derived |
| --- | --- | --- | --- | --- |
| baseline | 0 | 169651 | — | no setFeature call |
| R1 | 1 | 191085 | +9.52% [+8.43, +11.29] | static count in the target file; every call is on the per-call path |
| R2 | 0 | 170058 | +1.45% [+0.67, +3.54] ≈ noise | no setFeature call |
| G1 | 4 | 254789 | +33.03% [+31.42, +35.07] | static count in the target file; every call is on the per-call path |
| G2 | 4 | 254804 | +33.46% [+31.37, +36.25] | static count in the target file; every call is on the per-call path |
| G3 | 4 | 254785 | +33.81% [+32.12, +36.39] | static count in the target file; every call is on the per-call path |
| G4 | 4 | 254803 | +33.94% [+32.53, +36.10] | static count in the target file; every call is on the per-call path |
| G5 | 4 | 254812 | +31.95% [+31.07, +34.23] | static count in the target file; every call is on the per-call path |
| P1 (post-hoc, T2 session) | 0 per operation (4 once, at class load) | 166227 | -6.60% [-7.67, -5.42] | factory configured once and reused; measured in its own session against that session's baseline |

Session: `step3-v3/C2` (allocation and latency from `measurement/summary.json`).

### C.9 v3 remeasurement with the current runner (D11, post-hoc)

`step3-v3/<case>`: the saved Step 3 candidates and the hand-written patches,
re-validated and re-measured with the current runner. Since D8, fork and check
working directories are on the Linux filesystem. No model call. Validation
outcomes are identical to v1 and v2. The v3 rows are in the cross-session
tables in B.3. Below, per arm: whether the v3 latency interval overlaps the
interval of each earlier session.

C1:

| Arm | v3 latency overhead [95% CI] | overlaps v1 Step 2 | overlaps v1 Step 3 | overlaps v2 Step 2 | overlaps v2 Step 3 |
| --- | --- | --- | --- | --- | --- |
| R1 | +4.37% [+1.97, +5.77] | yes | yes | yes | yes |
| R2 | -63.11% [-63.87, -62.54] | yes | yes | yes | yes |

C2:

| Arm | v3 latency overhead [95% CI] | overlaps v1 Step 2 | overlaps v1 Step 3 | overlaps v2 Step 2 | overlaps v2 Step 3 |
| --- | --- | --- | --- | --- | --- |
| R1 | +9.52% [+8.43, +11.29] | yes | yes | yes | yes |
| R2 | +1.45% [+0.67, +3.54] ≈ noise | yes | yes | yes | yes |
| G1 | +33.03% [+31.42, +35.07] | not measured | yes | not measured | yes |
| G2 | +33.46% [+31.37, +36.25] | not measured | yes | not measured | yes |
| G3 | +33.81% [+32.12, +36.39] | not measured | yes | not measured | yes |
| G4 | +33.94% [+32.53, +36.10] | not measured | yes | not measured | yes |
| G5 | +31.95% [+31.07, +34.23] | not measured | yes | not measured | yes |

v3 budget decisions, C1:

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2 | R2 | R1: latency overhead upper bound 5.77% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

v3 budget decisions, C2:

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G1, G2, G3, G4, G5 | R2 | R2 | R1: latency overhead upper bound 11.29% > cap 5.0%; G1: latency overhead upper bound 35.07% > cap 5.0%; G2: latency overhead upper bound 36.25% > cap 5.0%; G3: latency overhead upper bound 36.39% > cap 5.0%; G4: latency overhead upper bound 36.10% > cap 5.0%; G5: latency overhead upper bound 34.23% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G1, G2, G3, G4, G5 | R2, R1 | R2 | G1: latency overhead upper bound 35.07% > cap 25.0%; G2: latency overhead upper bound 36.25% > cap 25.0%; G3: latency overhead upper bound 36.39% > cap 25.0%; G4: latency overhead upper bound 36.10% > cap 25.0%; G5: latency overhead upper bound 34.23% > cap 25.0% |

### C.10 Post-hoc arm P1 for C2 (D12) — post-hoc, designed after seeing results

P1 is **not a reference fix** and enters no decision table. It is hand-written
from the original C2 source (`posthoc/C2-P1/`). It uses the same four feature
settings and the same two setters as generated candidate G2. The difference:
the configured `DocumentBuilderFactory` is built once at class load and
reused, and each call takes a new `DocumentBuilder` from it under a lock. It
was validated with the registered C2 checks and measured in its own session
with baseline, baseline-AA, R1 and G2 (`posthoc/C2-P1-session/`).

| Arm | Registered checks (claim level) | Inputs now rejected | Median latency (ns/op) | Median alloc (B/op) | Latency vs baseline [95% CI] | Peak memory vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | L2 | 0 | 61108.6 | 169653 | — | — |
| baseline-AA | (copy of V0) | — | 61930.5 | 169649 | +1.34% [+0.08, +2.86] ≈ noise | +1.07% [-1.59, +3.21] ≈ noise |
| R1 | L4 | 4 | 67206.8 | 191083 | +9.98% [+8.85, +11.90] | +1.29% [-3.61, +3.17] ≈ noise |
| G2 | L4 | 4 | 82377.4 | 254824 | +34.80% [+33.19, +37.23] | -1.83% [-5.25, +0.71] ≈ noise |
| P1 | L4 | 4 | 57074.8 | 166227 | -6.60% [-7.67, -5.42] | -3.41% [-5.54, -1.67] |

A/A noise floor: latency 2.86%, peak memory 3.21%. Raw samples `posthoc/C2-P1-session/measurement/raw_samples.jsonl` sha256 `221d6c8340cd20b6b41a5e84bd1df286dabbb356f41d779c4485ff018e6fb3e2`.

| Comparison (same session) | Latency [95% CI] | Peak memory [95% CI] |
| --- | --- | --- |
| P1 vs R1 | -15.08% [-16.45, -14.23] | -4.64% [-5.87, +0.05] |
| P1 vs G2 | -30.72% [-31.84, -29.96] | -1.60% [-3.63, +1.76] |
| G2 vs R1 | +22.57% [+20.60, +24.50] | -3.09% [-6.31, +1.87] |

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
at 18:36:25 PST, inside the 4-hour limit.

### D.1 Generator-free part (primary evidence; committed as `2ac5656`)

R1 = upstream fix (three files), R2 = OWASP DOM defense (hand-written),
CONTROL = incomplete (hand-written).

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (parsed document) | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 0/6 |
| R2 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `3c730c9367cb7982f43fafb443aaa63dabecd3b6be5a4b40662aee11e05a8d34`.

A/A noise floor: latency **5.77%**, peak memory **5.86%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 56426.0 | 100850 | 132161 | — | — |
| baseline-AA | 20/20 | 55697.3 | 99684 | 132166 | -1.29% [-5.77, +3.93] ≈ noise | -1.16% [-5.86, +5.47] ≈ noise |
| R1 | 20/20 | 78306.0 | 105964 | 217436 | +38.78% [+33.34, +45.92] | +5.07% [+0.53, +10.63] ≈ noise |
| R2 | 20/20 | 62336.5 | 106052 | 153684 | +10.47% [+4.42, +15.44] | +5.16% [+1.24, +10.33] ≈ noise |

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | none | none | R1: latency overhead upper bound 45.92% > cap 5.0%, peak-memory overhead upper bound 10.63% > cap 5.0%; R2: latency overhead upper bound 15.44% > cap 5.0%, peak-memory overhead upper bound 10.33% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2 | R2 | R1: latency overhead upper bound 45.92% > cap 25.0% |

R1 and R2 were measured again in each generator session (same protocol):

| Session | Arm | Latency overhead [95% CI] | Peak-memory overhead [95% CI] | A/A noise floor (lat / mem) | Strict | Lenient |
| --- | --- | --- | --- | --- | --- | --- |
| no generator | R1 | +38.78% [+33.34, +45.92] | +5.07% [+0.53, +10.63] ≈ noise | 5.77% / 5.86% | no | no |
| no generator | R2 | +10.47% [+4.42, +15.44] | +5.16% [+1.24, +10.33] ≈ noise | 5.77% / 5.86% | no | fits (recommended) |
| frozen-settings run | R1 | +40.87% [+37.96, +42.79] | +7.48% [+4.10, +10.01] | 1.82% / 4.40% | no | no |
| frozen-settings run | R2 | +11.39% [+9.08, +13.10] | +7.21% [+3.83, +9.94] | 1.82% / 4.40% | no | fits (recommended) |
| long-context run | R1 | +40.51% [+37.56, +42.77] | +11.01% [+5.13, +14.07] | 2.93% / 6.22% | no | no |
| long-context run | R2 | +11.13% [+8.89, +12.89] | +7.84% [+2.46, +10.01] | 2.93% / 6.22% | no | fits (recommended) |
| long-context run | G2 | +81.44% [+77.61, +85.58] | +11.02% [+5.53, +12.26] | 2.93% / 6.22% | no | no |
| long-context run | G3 | +81.79% [+77.82, +84.91] | +10.50% [+5.05, +11.97] | 2.93% / 6.22% | no | no |
| long-context run | G5 | +83.62% [+79.61, +89.75] | +11.57% [+6.27, +12.81] | 2.93% / 6.22% | no | no |

### D.2 Generator part, frozen settings (primary generator result): prompt truncation

Result: **prompt truncation**. The server cut every prompt to fit the frozen
context, so no candidate could be a patch (L0 5/5, L1 0/5). This shows the
frozen settings do not fit a 46 KB file. It says nothing about the model's
behavior on the full prompt.

Exactly the Step 3 prompt template and settings (8,192-token context, 4,096
`max_tokens`). The full prompt is 10,075 tokens; the server log records
`truncating input prompt limit=4098 prompt=10075` for every request, so the
model saw only the last 4,098 tokens of the file and not the instructions.

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 19.69 | 4098 | 2048 | stop | `7900d982084d5adc…` | L0 |
| G2 | 102 | 3.37 | 4098 | 464 | stop | `0f27551d6d825169…` | L0 |
| G3 | 103 | 1.22 | 4098 | 164 | stop | `1f499b985d22fb5a…` | L0 |
| G4 | 104 | 3.84 | 4098 | 528 | stop | `acc13289a5e30733…` | L0 |
| G5 | 105 | 4.03 | 4098 | 559 | stop | `760fa1ba8e925e26…` | L0 |

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

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | 5/5 | 5/5 | 5/5 | 3/5 | 3/5 | 0/5 | 0/5 |

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 87.73 | 10075 | 9934 | stop | `784921689c1f5898…` | L2 |
| G2 | 102 | 80.73 | 10075 | 10112 | stop | `77305c3c27b618a1…` | L4 |
| G3 | 103 | 81.80 | 10075 | 10128 | stop | `9ebc9cf3b889ab46…` | L4 |
| G4 | 104 | 80.25 | 10075 | 9935 | stop | `27d71801f32cf18b…` | L2 |
| G5 | 105 | 80.00 | 10075 | 10128 | stop | `246cfdd6f7f4d1de…` | L4 |

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (parsed document) | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 0/6 |
| R2 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G1 | yes | FIRES (parsed document) | FIRES (parsed document) | FIRES (parsed document) | 2 of 34 functional tests fail: ['testElementBefore(com.jamesmurty.utils.TestXMLBuilder)', 'testElementBefore(com.jamesmurty.utils.TestXMLBuilder2)'] | L2 | 0/6 |
| G2 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G3 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G4 | yes | FIRES (parsed document) | FIRES (parsed document) | FIRES (parsed document) | 2 of 34 functional tests fail: ['testElementBefore(com.jamesmurty.utils.TestXMLBuilder)', 'testElementBefore(com.jamesmurty.utils.TestXMLBuilder2)'] | L2 | 0/6 |
| G5 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2, G2, G3, G5; raw samples `raw_samples.jsonl` sha256 `5aefdc587cb04548c484fd7c287923a71f6a8051eda296db87e3833f30aaaf31`.

A/A noise floor: latency **2.93%**, peak memory **6.22%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 54636.9 | 97366 | 132345 | — | — |
| baseline-AA | 20/20 | 55341.1 | 99524 | 132375 | +1.29% [-1.08, +2.93] ≈ noise | +2.22% [-3.50, +6.22] ≈ noise |
| R1 | 20/20 | 76770.4 | 108082 | 217583 | +40.51% [+37.56, +42.77] | +11.01% [+5.13, +14.07] |
| R2 | 20/20 | 60720.4 | 105000 | 153819 | +11.13% [+8.89, +12.89] | +7.84% [+2.46, +10.01] |
| G2 | 20/20 | 99134.4 | 108100 | 302907 | +81.44% [+77.61, +85.58] | +11.02% [+5.53, +12.26] |
| G3 | 20/20 | 99322.9 | 107586 | 302915 | +81.79% [+77.82, +84.91] | +10.50% [+5.05, +11.97] |
| G5 | 20/20 | 100326.6 | 108630 | 302911 | +83.62% [+79.61, +89.75] | +11.57% [+6.27, +12.81] |

Excess over matched reference (formerly "model-induced cost"; D14). The
pre-registered rule matches G2, G3 and G5 to R2 because each sets
`disallow-doctype-decl`. R2 sets that one feature (plus
`FEATURE_SECURE_PROCESSING`) on the parse factory only. The candidates set
four features and further setters on both the parse and the create factory
(see C.8). So the excess measures a different configuration and is not
attributed to the model:

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (excess over matched reference) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G2 | R2 | +81.44% [+77.61, +85.58] | +63.26% [+60.37, +66.96] | +2.95% [+0.66, +4.67] ≈ noise |
| G3 | R2 | +81.79% [+77.82, +84.91] | +63.57% [+60.89, +66.13] | +2.46% [-0.10, +4.38] ≈ noise |
| G5 | R2 | +83.62% [+79.61, +89.75] | +65.23% [+62.41, +70.64] | +3.46% [+1.28, +5.10] ≈ noise |

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G2, G3, G5 | none | none | R1: latency overhead upper bound 42.77% > cap 5.0%, peak-memory overhead upper bound 14.07% > cap 5.0%; R2: latency overhead upper bound 12.89% > cap 5.0%, peak-memory overhead upper bound 10.01% > cap 5.0%; G2: latency overhead upper bound 85.58% > cap 5.0%, peak-memory overhead upper bound 12.26% > cap 5.0%; G3: latency overhead upper bound 84.91% > cap 5.0%, peak-memory overhead upper bound 11.97% > cap 5.0%; G5: latency overhead upper bound 89.75% > cap 5.0%, peak-memory overhead upper bound 12.81% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G2, G3, G5 | R2 | R2 | R1: latency overhead upper bound 42.77% > cap 25.0%; G2: latency overhead upper bound 85.58% > cap 25.0%; G3: latency overhead upper bound 84.91% > cap 25.0%; G5: latency overhead upper bound 89.75% > cap 25.0% |

Observed (no candidate was edited): G2, G3 and G5 add
`disallow-doctype-decl` plus `external-general-entities`,
`external-parameter-entities` and `load-external-dtd` set to false to both
the parse and the create factory (G3 and G5 also
`setExpandEntityReferences(false)`). G1 and G4 add no security setting; both
change `isNamespaceAware` from `true` to `false` and reword comments, which
fails `testElementBefore` in both test classes and leaves every canary
firing.

Summary of D.3, from the tables above: under the declared long-context
variant the default local generator reached L4 on L1 for 3 of 5 candidates
(G2, G3, G5). Each costs about +81% to +84% latency against the unpatched
library (upper bounds 84.91% to 89.75%), about +63% to +65% against R2 (the
reference with the same mechanism, measured in the same session), and fits
neither budget. In the same session the upstream fix R1 costs +40.51% and the
OWASP fix R2 +11.13%; nothing fits the strict budget and only R2 fits the
lenient one. Generation took about 80 to 88 s per candidate on the GPU for
about 10,000 completion tokens each.

### D.4 Supplementary observation: is an external DTD named by the document read? (D13, post-hoc)

Not a check and not part of any claim level. The document's DOCTYPE names a
local DTD file that declares an **internal** entity holding a marker string,
and the body uses the entity (`posthoc/L1-dtd-observation/`). If the marker
appears in the parsed document, the parser read the external DTD. One fresh
JVM per patch, same library build layout as validation; no model call.

| Patch | Observation | Detail (truncated) |
| --- | --- | --- |
| V0 | DTD loaded (marker present) | text content: PARAPET-DTD-LOADED-3f8a / serialized: <config><name>PARAPET-DTD-LOADED-3f8a</name></config> |
| CONTROL | DTD loaded (marker present) | text content: PARAPET-DTD-LOADED-3f8a / serialized: <config><name>PARAPET-DTD-LOADED-3f8a</name></config> |
| R1 | DTD loaded (marker present) | text content: PARAPET-DTD-LOADED-3f8a / serialized: <config><name>PARAPET-DTD-LOADED-3f8a</name></config> |
| R2 | document rejected | org.xml.sax.SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true. |
| G2 | document rejected | org.xml.sax.SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true. |
| G3 | document rejected | org.xml.sax.SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true. |
| G5 | document rejected | org.xml.sax.SAXParseException: DOCTYPE is disallowed when the feature "http://apache.org/xml/features/disallow-doctype-decl" set to true. |

### D.5 setFeature calls, allocation and latency for L1 (D14, post-hoc analysis)

Per workload operation the driver calls `XMLBuilder.parse` and
`XMLBuilder.create` once each, so both `parseDocumentImpl` and
`createDocumentImpl` build a factory. Session: long-context run.

| Patch | setFeature calls per workload operation (excl. FEATURE_SECURE_PROCESSING) | Median allocation per operation (bytes) | Latency overhead vs baseline [95% CI] | How the count was derived |
| --- | --- | --- | --- | --- |
| baseline | 0 | 132345 | — | static count in parseDocumentImpl (0) + createDocumentImpl (0); no loops |
| R1 | 4 (2 per factory: parse and create) | 217583 | +40.51% [+37.56, +42.77] | upstream helper loops over three feature URIs per feature and stops at the first that succeeds; on this JDK the first succeeds, so 2 calls per factory; the workload builds 2 factories per operation |
| R2 | 1 | 153819 | +11.13% [+8.89, +12.89] | static count in parseDocumentImpl (1) + createDocumentImpl (0); no loops |
| G2 | 8 | 302907 | +81.44% [+77.61, +85.58] | static count in parseDocumentImpl (4) + createDocumentImpl (4); no loops |
| G3 | 8 | 302915 | +81.79% [+77.82, +84.91] | static count in parseDocumentImpl (4) + createDocumentImpl (4); no loops |
| G5 | 8 | 302911 | +83.62% [+79.61, +89.75] | static count in parseDocumentImpl (4) + createDocumentImpl (4); no loops |

Session: `step4/L1-gen-longctx` (allocation and latency from `measurement/summary.json`).

Endpoint logs (model calls, Step 4):

Frozen settings:

| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-18T18:16:06-0800 | GET | `http://127.0.0.1:11434/api/version` | model metadata |  | ok | 0.006 |
| 2026-11-18T18:16:06-0800 | GET | `http://127.0.0.1:11434/api/tags` | model metadata |  | ok | 0.004 |
| 2026-11-18T18:16:06-0800 | POST | `http://127.0.0.1:11434/api/show` | model metadata |  | ok | 0.001 |
| 2026-11-18T18:16:25-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 101 | ok | 19.687 |
| 2026-11-18T18:16:29-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 102 | ok | 3.368 |
| 2026-11-18T18:16:30-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 103 | ok | 1.221 |
| 2026-11-18T18:16:34-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 104 | ok | 3.843 |
| 2026-11-18T18:16:38-0800 | POST | `http://127.0.0.1:11434/v1/chat/completions` | candidate generation | 105 | ok | 4.029 |

Long-context variant:

| Time | Method | Endpoint | Purpose | Seed | Status | Duration (s) |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-18T18:19:57-0800 | GET | `http://127.0.0.1:11436/api/version` | model metadata |  | ok | 0.005 |
| 2026-11-18T18:19:57-0800 | GET | `http://127.0.0.1:11436/api/tags` | model metadata |  | ok | 0.001 |
| 2026-11-18T18:19:57-0800 | POST | `http://127.0.0.1:11436/api/show` | model metadata |  | ok | 0.021 |
| 2026-11-18T18:21:25-0800 | POST | `http://127.0.0.1:11436/v1/chat/completions` | candidate generation | 101 | ok | 87.731 |
| 2026-11-18T18:22:46-0800 | POST | `http://127.0.0.1:11436/v1/chat/completions` | candidate generation | 102 | ok | 80.726 |
| 2026-11-18T18:24:07-0800 | POST | `http://127.0.0.1:11436/v1/chat/completions` | candidate generation | 103 | ok | 81.804 |
| 2026-11-18T18:25:28-0800 | POST | `http://127.0.0.1:11436/v1/chat/completions` | candidate generation | 104 | ok | 80.252 |
| 2026-11-18T18:26:48-0800 | POST | `http://127.0.0.1:11436/v1/chat/completions` | candidate generation | 105 | ok | 80.003 |

The re-measurement made no model request. A connection monitor (`ss`, every
2 s, `logs/ollama_connections_step4.log`) covered the Step 4 generation runs
and saw only loopback-to-loopback connections for the Ollama processes.

GPU board power during Step 4 generation (long-context variant):

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 436 | 281.1 | 407.5 | 24620 |
| G2 | 402 | 313.6 | 316.8 | 25292 |
| G3 | 406 | 311.9 | 316.9 | 25413 |
| G4 | 398 | 311.0 | 317.5 | 24918 |
| G5 | 398 | 315.3 | 318.9 | 25177 |

First samples before the first request (board idle plus desktop): 60.9, 61.3, 61.8 W. 2040 samples at 200 ms from `generation/gpu_power.csv`.

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

### Deviations log — mozilla/local-slice

Every change to pre-registered material after the `prereg:` commit is
recorded here with its reason and time, and results are reported for both
versions. Section 1 records things a reader should know that happened BEFORE
the pre-registration commit.

#### 1. Disclosures made before pre-registration

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

#### 2. Deviations after pre-registration

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

#### 3. Step 4 (after LOCAL-EVIDENCE `fe998326ff39b3ed3bb47a5e4081e3b6e415ad05`)

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

#### 4. Post-hoc tasks after the final evidence commit `8c8ad50` (requested 2026-11-18, started 19:05 PST)

All four are **post-hoc**: designed and run after the results above were
seen. No model was called. No case, check, budget, decision rule, claim
level, `LOCAL-EVIDENCE.md`, or existing run directory was changed;
`LOCAL-EVIDENCE.md` still rebuilds byte-identically from its template.

**D11 (post-hoc). v3 remeasurement of C1 and C2 (19:05:32–19:13:28 PST).**
`python -m parapet run --case <C> --candidates-from
evidence/mozilla-2026-11/step3/<C>/generation --budget
parapet/budgets/strict.parapet.budget.yaml --budget
parapet/budgets/lenient.parapet.budget.yaml`, written to `step3-v3/<C>/`,
with the current runner (D6 memory fix; D8 Linux working directories).
Validation outcomes are identical to v1 and v2. Every v3 latency interval
overlaps the interval of every earlier session in which that arm was
measured. One verdict changed relative to the earlier sessions: C1 R1's
latency upper bound is 5.77%, so in v3 it does not fit the strict budget
(R2 still fits and is recommended). C2 R2 fits the strict budget in v3. v3
rows are added to the cross-session tables in EVIDENCE.md (builder kind
`cross_v3`; the `cross` kind used by LOCAL-EVIDENCE.md is unchanged).

**D12 (post-hoc, designed after seeing results). C2 arm P1 (19:13:52–19:16:40 PST).**
P1 (`posthoc/C2-P1/`) is hand-written from the original C2 source, not from
G2's file. It applies the same four `setFeature` calls and two setters as
generated candidate G2 to a `DocumentBuilderFactory` built once at class load
and reused (`newDocumentBuilder` under a lock). It is not a reference fix,
enters no decision table, and no budget was applied. It was validated with
the registered C2 checks (L4; the same four DTD probes rejected as R1 and G2)
and measured in its own session with baseline, baseline-AA, R1 and G2
(`analysis/posthoc_c2_p1.py`, output `posthoc/C2-P1-session/`). Latency
against that session's baseline: P1 -6.60% [-7.67, -5.42], G2 +34.80%
[+33.19, +37.23], R1 +9.98% [+8.85, +11.90]. P1 against G2: -30.72%
[-31.84, -29.96]. P1 and G2 differ only in whether the configured factory is
built per call or once.

**D13 (post-hoc). L1 external-DTD observation (19:13:38–19:13:45 PST).** A
supplementary program (`posthoc/L1-dtd-observation/`), not a check and not part of any claim level. It
parses a document whose DOCTYPE names a local DTD file declaring an internal
entity that holds a marker, with the entity used in the body. It was run
against V0, CONTROL, R1, R2 (case files) and G2, G3, G5 (saved candidates).
Observed: V0, CONTROL and R1 load the DTD (marker present); R2, G2, G3 and
G5 reject the document (DOCTYPE disallowed). Section H's sentence on
external DTDs was corrected to state this observation instead of the earlier
inference from the benign external-DTD probe.

**D14 (post-hoc). Analysis and wording only, from existing summaries.**
(a) Tables of setFeature calls per workload operation (excluding
`FEATURE_SECURE_PROCESSING`), median allocation per operation and latency
overhead, per case (`analysis/posthoc_tables.py`); counts are read from patch
sources, and for L1 R1 from the upstream helper's loop (first feature URI
succeeds on this JDK). (b) "Model-induced cost" is renamed "excess over
matched reference" in EVIDENCE.md. The matched reference sets fewer features
than the candidates, so the excess is not attributed to the model. Existing
records, run summaries and LOCAL-EVIDENCE.md keep the old label, which is
superseded; they are not rewritten. (c) L1's frozen-settings result is
described as prompt truncation. (d) Sessions whose A/A peak-memory upper
bound exceeds 5% are listed, and their strict memory verdicts are marked not
resolvable (EVIDENCE.md B.4); the recorded `decision.json` files are
unchanged. (e) EVIDENCE.md states that L4 means "passes the registered
checks" and that L4 patches can differ in security coverage.

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

Command (repository root, at the final commit):

```bash
PYTHON=~/parapet-work/venv/bin/python ./scripts/run_tests.sh
```

Result (2026-11-18 18:37 PST): **445 passed, 0 failed, 0 skipped**:
component functional and Python runtime smoke tests 242 passed; Java/JVM
end-to-end tests 8 passed; repository and website structural checks 195
passed. ("Deselected" counts are the `jvm` marker split between suites, not
skips.) `tests/parapet/test_prompt_and_generator.py::test_library_case_prompt_reads_only_the_target_file`
ran here because the L1 jars are present; on a runner without them (CI) it
skips by design. At LOCAL-EVIDENCE the same command gave 444 passed, 0
failed, 0 skipped. Raw output: `logs/run_tests_final.log`,
`logs/run_tests_local_evidence.log`.

```text
=== Component functional and Python runtime smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/more_than_just_functional tests/parapet -m not jvm
====================== 242 passed, 8 deselected in 3.97s =======================
=== Java/JVM end-to-end smoke tests ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/perforch tests/parapet -m jvm
====================== 8 passed, 218 deselected in 25.37s ======================
=== Repository and website structural checks ===
$ /home/yzhao/parapet-work/venv/bin/python -m pytest tests/repository tests/website
============================= 195 passed in 2.34s ==============================
All selected PARAPET checks passed.
```

## J. One line per case

- **C1 (CWE-502, authored):** the default local generator did not reach L4 (0/5; best L2, 1/5). An admissible patch fits the strict budget: yes, hand-written R2 in every session (5/5) and R1 in four of five (not in the post-hoc v3 session). Lenient: yes, R1 and R2 in every session. No generated patch fits either budget.
- **C2 (CWE-611, authored):** the default local generator reached L4 (5/5). An admissible patch fits the strict budget: hand-written R2 only, in four of five sessions including the post-hoc v3 session (in the v2 Step 2 session nothing fits). Lenient: yes, R1 and R2 in every session. No generated patch fits either budget.
- **L1 (CWE-611, java-xmlbuilder):** under the frozen settings the default local generator did not reach L4 (0/5): prompt truncation, nothing parseable. Under the declared long-context variant it reached L4 (3/5). An admissible patch fits the strict budget: no, in no session (every patch misses on latency; strict memory verdicts are not resolvable in the L1 sessions listed in B.4). Lenient: yes, hand-written R2 only. The upstream fix R1 and every generated patch fit neither budget.

---

Branch: `mozilla/local-slice`
LOCAL-EVIDENCE: `fe998326ff39b3ed3bb47a5e4081e3b6e415ad05`
Final: `eca25f47a83189ad1fed08f66b322d7c0090aba2` — the last evidence commit before this file; the commit that adds this file is the head of `mozilla/local-slice` (`git rev-parse mozilla/local-slice`).
