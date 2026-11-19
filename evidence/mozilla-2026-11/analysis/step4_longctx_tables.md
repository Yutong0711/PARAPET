### L1 — `step4/L1-gen-longctx`

Commit `2ac56563e219`, generator used: True, phases {'generate_s': 0.2, 'validate_s': 44.6, 'measure_s': 319.0}.

**Claim levels (generated candidates, k = 5)**

| Case | L0 server answers | L1 parseable patch | L2 compiles | L3 reproducer no longer fires | L4 admissible | L5 fits strict | L5 fits lenient |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 | 5/5 | 5/5 | 5/5 | 3/5 | 3/5 | 0/5 | 0/5 |

**Generation (time and tokens per candidate)**

| Candidate | Seed | Wall-clock (s) | Prompt tokens | Completion tokens | Finish | Raw output sha256 | Highest claim level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | 87.73 | 10075 | 9934 | stop | `784921689c1f5898…` | L2 |
| G2 | 102 | 80.73 | 10075 | 10112 | stop | `77305c3c27b618a1…` | L4 |
| G3 | 103 | 81.80 | 10075 | 10128 | stop | `9ebc9cf3b889ab46…` | L4 |
| G4 | 104 | 80.25 | 10075 | 9935 | stop | `27d71801f32cf18b…` | L2 |
| G5 | 105 | 80.00 | 10075 | 10128 | stop | `246cfdd6f7f4d1de…` | L4 |

**Validation**

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

**Measurement**

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

**Model-induced cost (candidate vs the reference fix with the same mechanism)**

| Candidate | Matched reference (rule) | Latency vs baseline [95% CI] | Latency vs matched reference [95% CI] (model-induced) | Peak memory vs matched reference [95% CI] |
| --- | --- | --- | --- | --- |
| G2 | R2 | +81.44% [+77.61, +85.58] | +63.26% [+60.37, +66.96] | +2.95% [+0.66, +4.67] ≈ noise |
| G3 | R2 | +81.79% [+77.82, +84.91] | +63.57% [+60.89, +66.13] | +2.46% [-0.10, +4.38] ≈ noise |
| G5 | R2 | +83.62% [+79.61, +89.75] | +65.23% [+62.41, +70.64] | +3.46% [+1.28, +5.10] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2, G2, G3, G5 | none | none | R1: latency overhead upper bound 42.77% > cap 5.0%, peak-memory overhead upper bound 14.07% > cap 5.0%; R2: latency overhead upper bound 12.89% > cap 5.0%, peak-memory overhead upper bound 10.01% > cap 5.0%; G2: latency overhead upper bound 85.58% > cap 5.0%, peak-memory overhead upper bound 12.26% > cap 5.0%; G3: latency overhead upper bound 84.91% > cap 5.0%, peak-memory overhead upper bound 11.97% > cap 5.0%; G5: latency overhead upper bound 89.75% > cap 5.0%, peak-memory overhead upper bound 12.81% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2, G2, G3, G5 | R2 | R2 | R1: latency overhead upper bound 42.77% > cap 25.0%; G2: latency overhead upper bound 85.58% > cap 25.0%; G3: latency overhead upper bound 84.91% > cap 25.0%; G5: latency overhead upper bound 89.75% > cap 25.0% |

**GPU board power during generation (Step 6)**

| Candidate | Samples in window | Mean board power (W) | Max (W) | Energy over sampled window (J, trapezoid) |
| --- | --- | --- | --- | --- |
| G1 | 436 | 281.1 | 407.5 | 24620 |
| G2 | 402 | 313.6 | 316.8 | 25292 |
| G3 | 406 | 311.9 | 316.9 | 25413 |
| G4 | 398 | 311.0 | 317.5 | 24918 |
| G5 | 398 | 315.3 | 318.9 | 25177 |

First samples before the first request (board idle plus desktop): 60.9, 61.3, 61.8 W. 2040 samples at 200 ms from `generation/gpu_power.csv`.

