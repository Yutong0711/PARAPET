### C1 — `evidence/mozilla-2026-11/step2-v2/C1`

Commit `a137f02c4678`, generator used: False, phases {'validate_s': 16.1, 'measure_s': 122.6}.

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (GadgetA.readObject) | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: probe_legacy_linkedlist.b64 |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 6/6: probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `a1c147bdf667a3679670b6481da7e6764d43bfb4e552180a6338a9eb979719be`.

A/A noise floor: latency **2.27%**, peak memory **1.91%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 12683.4 | 104156 | 39793 | — | — |
| baseline-AA | 20/20 | 12585.4 | 103264 | 39809 | -0.77% [-2.27, +1.01] ≈ noise | -0.86% [-1.91, +0.48] ≈ noise |
| R1 | 20/20 | 13005.5 | 102658 | 41517 | +2.54% [+0.74, +3.78] | -1.44% [-4.04, +0.30] ≈ noise |
| R2 | 20/20 | 4635.9 | 76198 | 27277 | -63.45% [-64.02, -63.09] | -26.84% [-27.31, -25.09] |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2, R1 | R2 | — |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

### C2 — `evidence/mozilla-2026-11/step2-v2/C2`

Commit `a137f02c4678`, generator used: False, phases {'validate_s': 15.9, 'measure_s': 121.5}.

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (result:config.name) | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: external_dtd_benign_local |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `4866dacfa3f1cd52ac8c20c978630f20b7caef291910699eadac08bfcecac798`.

A/A noise floor: latency **2.72%**, peak memory **3.55%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 63067.5 | 111730 | 169645 | — | — |
| baseline-AA | 20/20 | 63552.4 | 110992 | 169637 | +0.77% [-2.05, +2.72] ≈ noise | -0.66% [-3.55, +2.68] ≈ noise |
| R1 | 20/20 | 69131.5 | 112334 | 191081 | +9.62% [+7.06, +11.48] | +0.54% [-2.74, +4.45] ≈ noise |
| R2 | 20/20 | 64329.2 | 111280 | 169977 | +2.00% [-0.64, +5.08] ≈ noise | -0.40% [-2.18, +4.68] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | none | none | R1: latency overhead upper bound 11.48% > cap 5.0%; R2: latency overhead upper bound 5.08% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

