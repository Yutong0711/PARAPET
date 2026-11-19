### C1 — `evidence/mozilla-2026-11/step3/C1`

Commit `5eefe0c1d143`, generator used: True, phases {'generate_s': 66.2, 'validate_s': 21.0, 'measure_s': 123.6}.

**Claim levels (generated candidates, k = 5)**

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | 5/5 | 5/5 | 1/5 | 0/5 | 0/5 | 0/5 | 0/5 |

**Generation (time and tokens per candidate)**

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 38.55 | 845 | 710 | stop | `0e9394a2da68cd7b…` | L2 |
| G2 | 102 | 6.33 | 845 | 902 | stop | `c8f9cdef50dbbf1d…` | L1 |
| G3 | 103 | 6.93 | 845 | 975 | stop | `632638d77cf93dd1…` | L1 |
| G4 | 104 | 6.25 | 845 | 849 | stop | `4e6ba5bed9b40c30…` | L1 |
| G5 | 105 | 7.46 | 845 | 1058 | stop | `693cd06806f6f993…` | L1 |

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (GadgetA.readObject) | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: probe_legacy_linkedlist.b64 |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 6/6: probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |
| G1 | yes | FIRES (GadgetA.readObject) | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L2 | 0/6 |
| G2 | NO | not run | not run | not run | not run | L1 | not run |
| G3 | NO | not run | not run | not run | not run | L1 | not run |
| G4 | NO | not run | not run | not run | not run | L1 | not run |
| G5 | NO | not run | not run | not run | not run | L1 | not run |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `05f759c3c0e5ad31ecd3f3afffa15374661b833fd486f0880f37ad52581ab975`.

A/A noise floor: latency **1.60%**, peak memory **2.33%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 12676.4 | 103518 | 39761 | — | — |
| baseline-AA | 20/20 | 12678.5 | 104180 | 39793 | +0.02% [-1.60, +1.55] ≈ noise | +0.64% [-0.56, +2.33] ≈ noise |
| R1 | 20/20 | 12895.3 | 101524 | 41517 | +1.73% [+0.51, +3.47] | -1.93% [-2.96, +0.50] ≈ noise |
| R2 | 20/20 | 4743.7 | 100832 | 27277 | -62.58% [-63.61, -61.78] | -2.59% [-3.22, -1.31] |

**Model-induced cost (candidate vs the reference fix with the same mechanism)**

No admissible generated candidate, so no model-induced cost to report.

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2, R1 | R2 | — |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

**GPU board power during generation (Step 6)**

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 190 | 68.6 | 313.7 | 2597 |
| G2 | 32 | 310.8 | 313.8 | 1938 |
| G3 | 34 | 310.1 | 318.5 | 2061 |
| G4 | 30 | 304.9 | 318.2 | 1837 |
| G5 | 37 | 315.1 | 318.6 | 2286 |

First samples before the first request (board idle plus desktop): 22.0, 22.1, 22.8 W. 323 samples at 200 ms from `generation/gpu_power.csv`.

### C2 — `evidence/mozilla-2026-11/step3/C2`

Commit `6dda2e9b974e`, generator used: True, phases {'generate_s': 21.0, 'validate_s': 34.3, 'measure_s': 312.1}.

**Claim levels (generated candidates, k = 5)**

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C2 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 0/5 | 0/5 |

**Generation (time and tokens per candidate)**

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 4.43 | 627 | 595 | stop | `514b0502cec45b6d…` | L4 |
| G2 | 102 | 4.04 | 627 | 587 | stop | `b298ef7d62e80430…` | L4 |
| G3 | 103 | 4.06 | 627 | 587 | stop | `d73163d4d23adb2d…` | L4 |
| G4 | 104 | 4.04 | 627 | 587 | stop | `d73163d4d23adb2d…` | L4 |
| G5 | 105 | 4.08 | 627 | 587 | stop | `b298ef7d62e80430…` | L4 |

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (result:config.name) | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: external_dtd_benign_local |
| G1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G3 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G4 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G5 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2, G1, G2, G3, G4, G5; raw samples `raw_samples.jsonl` sha256 `2fdebe785cdfac375cf49146461f1c77c6cdfa1c2b1cfab76f52eeedee07400c`.

A/A noise floor: latency **4.32%**, peak memory **3.69%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 62758.6 | 111338 | 169601 | — | — |
| baseline-AA | 20/20 | 63447.5 | 112034 | 169625 | +1.10% [-0.96, +4.32] ≈ noise | +0.63% [-3.69, +2.16] ≈ noise |
| R1 | 20/20 | 69577.2 | 112036 | 191046 | +10.86% [+8.16, +14.52] | +0.63% [-3.50, +3.02] ≈ noise |
| R2 | 20/20 | 64671.9 | 111450 | 170040 | +3.05% [+0.93, +4.84] ≈ noise | +0.10% [-2.96, +3.78] ≈ noise |
| G1 | 20/20 | 84319.6 | 109390 | 254799 | +34.36% [+31.45, +39.84] | -1.75% [-5.43, +0.35] ≈ noise |
| G2 | 20/20 | 85894.3 | 111688 | 254814 | +36.86% [+32.93, +41.07] | +0.31% [-4.05, +2.73] ≈ noise |
| G3 | 20/20 | 84841.1 | 109276 | 254790 | +35.19% [+32.12, +39.89] | -1.85% [-5.15, -0.72] ≈ noise |
| G4 | 20/20 | 84570.1 | 108738 | 254801 | +34.75% [+31.60, +37.73] | -2.34% [-5.55, -1.03] ≈ noise |
| G5 | 20/20 | 83936.4 | 110420 | 254783 | +33.74% [+30.64, +35.75] | -0.82% [-5.28, +2.83] ≈ noise |

**Model-induced cost (candidate vs the reference fix with the same mechanism)**

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +34.36% [+31.45, +39.84] | +21.19% [+17.50, +26.25] | -2.36% [-5.51, +1.43] ≈ noise |
| G2 | R1 | +36.86% [+32.93, +41.07] | +23.45% [+18.93, +27.34] | -0.31% [-4.35, +3.55] ≈ noise |
| G3 | R1 | +35.19% [+32.12, +39.89] | +21.94% [+18.14, +26.36] | -2.46% [-5.45, +0.84] ≈ noise |
| G4 | R1 | +34.75% [+31.60, +37.73] | +21.55% [+17.61, +24.52] | -2.94% [-5.60, +0.35] ≈ noise |
| G5 | R1 | +33.74% [+30.64, +35.75] | +20.64% [+16.64, +22.82] | -1.44% [-5.15, +3.50] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G1, G2, G3, G4, G5 | R2 | R2 | R1: latency overhead upper bound 14.52% > cap 5.0%; G1: latency overhead upper bound 39.84% > cap 5.0%; G2: latency overhead upper bound 41.07% > cap 5.0%; G3: latency overhead upper bound 39.89% > cap 5.0%; G4: latency overhead upper bound 37.73% > cap 5.0%; G5: latency overhead upper bound 35.75% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G1, G2, G3, G4, G5 | R2, R1 | R2 | G1: latency overhead upper bound 39.84% > cap 25.0%; G2: latency overhead upper bound 41.07% > cap 25.0%; G3: latency overhead upper bound 39.89% > cap 25.0%; G4: latency overhead upper bound 37.73% > cap 25.0%; G5: latency overhead upper bound 35.75% > cap 25.0% |

**GPU board power during generation (Step 6)**

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 22 | 242.1 | 306.9 | 1039 |
| G2 | 20 | 305.5 | 307.7 | 1168 |
| G3 | 21 | 306.2 | 307.9 | 1232 |
| G4 | 20 | 307.4 | 309.9 | 1176 |
| G5 | 20 | 307.1 | 308.3 | 1174 |

First samples before the first request (board idle plus desktop): 21.1, 21.7, 44.4 W. 103 samples at 200 ms from `generation/gpu_power.csv`.

