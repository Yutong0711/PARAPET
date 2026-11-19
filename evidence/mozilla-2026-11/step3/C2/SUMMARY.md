# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: True
- Commit: `6dda2e9b974ea5218acb26807d2a3aa876a60500` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3-C2-20261118T172012`

## Generation

| Candidate | Seed | Status | Wall s | Prompt tok | Completion tok | Finish | L1 | Extraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | success | 4.434 | 627 | 595 | stop | True | fenced code block #1 (java) declaring class ConfigLoader |
| G2 | 102 | success | 4.042 | 627 | 587 | stop | True | fenced code block #1 (java) declaring class ConfigLoader |
| G3 | 103 | success | 4.058 | 627 | 587 | stop | True | fenced code block #1 (java) declaring class ConfigLoader |
| G4 | 104 | success | 4.044 | 627 | 587 | stop | True | fenced code block #1 (java) declaring class ConfigLoader |
| G5 | 105 | success | 4.077 | 627 | 587 | stop | True | fenced code block #1 (java) declaring class ConfigLoader |

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | external_dtd_benign_local |
| G1 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G2 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G3 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G4 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G5 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 4.32%, peak memory 3.69%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 62758.6 | 111338 | — | — | — |
| baseline-AA | 20 | 63447.5 | 112034 | +1.10% [-0.96, +4.32] (indistinguishable) | +0.63% [-3.69, +2.16] (indistinguishable) | — |
| R1 | 20 | 69577.2 | 112036 | +10.86% [+8.16, +14.52] | +0.63% [-3.50, +3.02] (indistinguishable) | — |
| R2 | 20 | 64671.9 | 111450 | +3.05% [+0.93, +4.84] (indistinguishable) | +0.10% [-2.96, +3.78] (indistinguishable) | — |
| G1 | 20 | 84319.6 | 109390 | +34.36% [+31.45, +39.84] | -1.75% [-5.43, +0.35] (indistinguishable) | R1: +21.19% [+17.50, +26.25] |
| G2 | 20 | 85894.3 | 111688 | +36.86% [+32.93, +41.07] | +0.31% [-4.05, +2.73] (indistinguishable) | R1: +23.45% [+18.93, +27.34] |
| G3 | 20 | 84841.1 | 109276 | +35.19% [+32.12, +39.89] | -1.85% [-5.15, -0.72] (indistinguishable) | R1: +21.94% [+18.14, +26.36] |
| G4 | 20 | 84570.1 | 108738 | +34.75% [+31.60, +37.73] | -2.34% [-5.55, -1.03] (indistinguishable) | R1: +21.55% [+17.61, +24.52] |
| G5 | 20 | 83936.4 | 110420 | +33.74% [+30.64, +35.75] | -0.82% [-5.28, +2.83] (indistinguishable) | R1: +20.64% [+16.64, +22.82] |

Raw samples: `measurement/raw_samples.jsonl` sha256 `2fdebe785cdfac375cf49146461f1c77c6cdfa1c2b1cfab76f52eeedee07400c`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 14.52% > cap 5.0%
  - G1: latency overhead upper bound 39.84% > cap 5.0%
  - G2: latency overhead upper bound 41.07% > cap 5.0%
  - G3: latency overhead upper bound 39.89% > cap 5.0%
  - G4: latency overhead upper bound 37.73% > cap 5.0%
  - G5: latency overhead upper bound 35.75% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
  - G1: latency overhead upper bound 39.84% > cap 25.0%
  - G2: latency overhead upper bound 41.07% > cap 25.0%
  - G3: latency overhead upper bound 39.89% > cap 25.0%
  - G4: latency overhead upper bound 37.73% > cap 25.0%
  - G5: latency overhead upper bound 35.75% > cap 25.0%
