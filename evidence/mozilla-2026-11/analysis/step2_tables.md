### C1 — `evidence/mozilla-2026-11/step2/C1`

Commit `08900879fc58`, generator used: False, phases {'validate_s': 16.1, 'measure_s': 122.4}.

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (GadgetA.readObject) | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (GadgetB.hashCode) | FIRES (GadgetC.readResolve) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: probe_legacy_linkedlist.b64 |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 6/6: probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `fa10b25430acf50639751e2b6132199345665e05adffb0f35f8791e08a790362`.

A/A noise floor: latency **1.23%**, peak memory **1.81%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 12634.0 | 103786 | 39773 | — | — |
| baseline-AA | 20/20 | 12661.1 | 104232 | 39773 | +0.21% [-1.23, +1.18] ≈ noise | +0.43% [-1.02, +1.81] ≈ noise |
| R1 | 20/20 | 12979.2 | 102206 | 41549 | +2.73% [+0.86, +4.24] | -1.52% [-4.32, +1.17] ≈ noise |
| R2 | 20/20 | 4682.5 | 76134 | 27277 | -62.94% [-63.55, -62.13] | -26.64% [-27.41, -25.44] |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2, R1 | R2 | — |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

### C2 — `evidence/mozilla-2026-11/step2/C2`

Commit `08900879fc58`, generator used: False, phases {'validate_s': 15.6, 'measure_s': 121.2}.

**Validation**

| Patch | Compiles | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Inputs now rejected (probes) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | yes | FIRES (result:config.name) | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L2 | 0/6 |
| CONTROL | yes | blocked | FIRES (result:config.name) | FIRES (result:config.name) | 11/11 functional tests pass | L3 | 0/6 |
| R1 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 4/6: doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | yes | blocked | blocked | blocked | 11/11 functional tests pass | L4 | 1/6: external_dtd_benign_local |

**Measurement**

Session: 20 forks per arm, arms baseline, baseline-AA, R1, R2; raw samples `raw_samples.jsonl` sha256 `0e718a2a514b9fbe181937f9cef5895f677367385b1b210c73c44f7b2c81dc91`.

A/A noise floor: latency **4.93%**, peak memory **3.65%**.

| Arm | Valid forks | Median latency (ns/op) | Median peak RSS (KiB) | Median alloc (B/op) | Latency overhead vs baseline [95% CI] | Peak-memory overhead vs baseline [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20/20 | 63080.0 | 112010 | 169561 | — | — |
| baseline-AA | 20/20 | 63729.3 | 112256 | 169609 | +1.03% [-4.93, +3.26] ≈ noise | +0.22% [-2.76, +3.65] ≈ noise |
| R1 | 20/20 | 69375.8 | 114776 | 191050 | +9.98% [+4.25, +11.96] | +2.47% [-1.81, +5.09] ≈ noise |
| R2 | 20/20 | 63898.1 | 109692 | 169941 | +1.30% [-3.75, +3.17] ≈ noise | -2.07% [-4.33, +3.36] ≈ noise |

**Budget decisions**

| Budget | Caps (latency %, peak memory %) | Admissible patches assessed | Fit | Recommended | Why the others do not fit |
| --- | --- | --- | --- | --- | --- |
| strict (`208491b8306d…`) | 5.0, 5.0 | R1, R2 | R2 | R2 | R1: latency overhead upper bound 11.96% > cap 5.0%, peak-memory overhead upper bound 5.09% > cap 5.0% |
| lenient (`fdada931cc93…`) | 25.0, 25.0 | R1, R2 | R2, R1 | R2 | — |

