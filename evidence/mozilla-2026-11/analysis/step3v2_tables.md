### C1 — `evidence/mozilla-2026-11/step3-v2/C1`

Commit `a137f02c4678`, generator used: True, phases {'generate_s': 0.1, 'validate_s': 21.2, 'measure_s': 122.8}.

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

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `983498a69b4661465f9088f50abcf8030fb7d994b7c7f6f9a64ba29decd7e9c9`.

A/A noise floor: latency **3.03%**, peak memory **2.08%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 12650.6 | 104176 | 39817 | — | — |
| baseline-AA | 20/20 | 12769.3 | 103562 | 39773 | +0.94% [-1.20, +3.03] ≈ noise | -0.59% [-2.08, +0.46] ≈ noise |
| R1 | 20/20 | 13063.3 | 102582 | 41549 | +3.26% [+2.21, +4.47] | -1.53% [-4.40, -0.06] ≈ noise |
| R2 | 20/20 | 4668.8 | 76720 | 27277 | -63.09% [-63.60, -62.39] | -26.36% [-27.97, -25.17] |

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

### C2 — `evidence/mozilla-2026-11/step3-v2/C2`

Commit `a137f02c4678`, generator used: True, phases {'generate_s': 0.3, 'validate_s': 35.1, 'measure_s': 313.9}.

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

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2, G1, G2, G3, G4, G5; raw samples `raw_samples.jsonl` sha256 `cef73943453a11b46f1ec73dcef7ae2ea599fa881d57b755cd6098796a223384`.

A/A noise floor: latency **2.99%**, peak memory **4.83%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 63012.5 | 110084 | 169621 | — | — |
| baseline-AA | 20/20 | 63746.8 | 111010 | 169643 | +1.17% [-0.74, +2.99] ≈ noise | +0.84% [-1.67, +4.83] ≈ noise |
| R1 | 20/20 | 69949.7 | 114302 | 191087 | +11.01% [+8.28, +15.47] | +3.83% [+0.30, +5.52] ≈ noise |
| R2 | 20/20 | 64486.4 | 112520 | 169952 | +2.34% [+0.39, +4.68] ≈ noise | +2.21% [-2.15, +4.42] ≈ noise |
| G1 | 20/20 | 85204.2 | 109224 | 254791 | +35.22% [+32.67, +38.26] | -0.78% [-3.80, +1.52] ≈ noise |
| G2 | 20/20 | 85985.1 | 109938 | 254794 | +36.46% [+33.07, +39.68] | -0.13% [-3.67, +4.02] ≈ noise |
| G3 | 20/20 | 85648.2 | 109606 | 254796 | +35.92% [+33.58, +41.09] | -0.43% [-4.21, +2.03] ≈ noise |
| G4 | 20/20 | 85375.6 | 112468 | 254813 | +35.49% [+31.89, +37.61] | +2.17% [-3.87, +4.77] ≈ noise |
| G5 | 20/20 | 84945.6 | 109372 | 254810 | +34.81% [+31.29, +38.92] | -0.65% [-4.44, +2.71] ≈ noise |

**Model-induced cost (candidate vs the reference fix with the same mechanism)**

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G1 | R1 | +35.22% [+32.67, +38.26] | +21.81% [+17.08, +25.36] | -4.44% [-6.96, -1.33] ≈ noise |
| G2 | R1 | +36.46% [+33.07, +39.68] | +22.92% [+17.88, +26.59] | -3.82% [-6.93, +0.83] ≈ noise |
| G3 | R1 | +35.92% [+33.58, +41.09] | +22.44% [+17.72, +27.52] | -4.11% [-7.25, -0.73] ≈ noise |
| G4 | R1 | +35.49% [+31.89, +37.61] | +22.05% [+17.07, +24.85] | -1.60% [-7.29, +1.89] ≈ noise |
| G5 | R1 | +34.81% [+31.29, +38.92] | +21.44% [+16.18, +25.50] | -4.31% [-8.09, +0.06] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G1, G2, G3, G4, G5 | R2 | R2 | R1: latency overhead upper bound 15.47% > cap 5.0%, peak-memory overhead upper bound 5.52% > cap 5.0%; G1: latency overhead upper bound 38.26% > cap 5.0%; G2: latency overhead upper bound 39.68% > cap 5.0%; G3: latency overhead upper bound 41.09% > cap 5.0%; G4: latency overhead upper bound 37.61% > cap 5.0%; G5: latency overhead upper bound 38.92% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G1, G2, G3, G4, G5 | R2, R1 | R2 | G1: latency overhead upper bound 38.26% > cap 25.0%; G2: latency overhead upper bound 39.68% > cap 25.0%; G3: latency overhead upper bound 41.09% > cap 25.0%; G4: latency overhead upper bound 37.61% > cap 25.0%; G5: latency overhead upper bound 38.92% > cap 25.0% |

**GPU board power during generation (Step 6)**

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 22 | 242.1 | 306.9 | 1039 |
| G2 | 20 | 305.5 | 307.7 | 1168 |
| G3 | 21 | 306.2 | 307.9 | 1232 |
| G4 | 20 | 307.4 | 309.9 | 1176 |
| G5 | 20 | 307.1 | 308.3 | 1174 |

First samples before the first request (board idle plus desktop): 21.1, 21.7, 44.4 W. 103 samples at 200 ms from `generation/gpu_power.csv`.

