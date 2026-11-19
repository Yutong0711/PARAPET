### L1 — `evidence/mozilla-2026-11/step4/L1-nogen`

Commit `083b7b8a66de`, generator used: False, phases {'validate_s': 21.7, 'measure_s': 152.7}.

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (parsed document) | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (parsed document) | FIRES (parsed document) | 34/34 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 0/6 |
| R2 | yes | blocked | blocked | blocked | 34/34 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `3c730c9367cb7982f43fafb443aaa63dabecd3b6be5a4b40662aee11e05a8d34`.

A/A noise floor: latency **5.77%**, peak memory **5.86%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 56426.0 | 100850 | 132161 | — | — |
| baseline-AA | 20/20 | 55697.3 | 99684 | 132166 | -1.29% [-5.77, +3.93] ≈ noise | -1.16% [-5.86, +5.47] ≈ noise |
| R1 | 20/20 | 78306.0 | 105964 | 217436 | +38.78% [+33.34, +45.92] | +5.07% [+0.53, +10.63] ≈ noise |
| R2 | 20/20 | 62336.5 | 106052 | 153684 | +10.47% [+4.42, +15.44] | +5.16% [+1.24, +10.33] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | none | none | R1: latency overhead upper bound 45.92% > cap 5.0%, peak-memory overhead upper bound 10.63% > cap 5.0%; R2: latency overhead upper bound 15.44% > cap 5.0%, peak-memory overhead upper bound 10.33% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2 | R2 | R1: latency overhead upper bound 45.92% > cap 25.0% |

