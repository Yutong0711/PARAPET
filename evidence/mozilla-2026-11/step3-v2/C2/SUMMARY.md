# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: True
- Commit: `a137f02c4678bde5889045623cbff42e007829a2` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3v2-C2-20261118T174928`

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

A/A noise floor: latency 2.99%, peak memory 4.83%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 63012.5 | 110084 | — | — | — |
| baseline-AA | 20 | 63746.8 | 111010 | +1.17% [-0.74, +2.99] (indistinguishable) | +0.84% [-1.67, +4.83] (indistinguishable) | — |
| R1 | 20 | 69949.7 | 114302 | +11.01% [+8.28, +15.47] | +3.83% [+0.30, +5.52] (indistinguishable) | — |
| R2 | 20 | 64486.4 | 112520 | +2.34% [+0.39, +4.68] (indistinguishable) | +2.21% [-2.15, +4.42] (indistinguishable) | — |
| G1 | 20 | 85204.2 | 109224 | +35.22% [+32.67, +38.26] | -0.78% [-3.80, +1.52] (indistinguishable) | R1: +21.81% [+17.08, +25.36] |
| G2 | 20 | 85985.1 | 109938 | +36.46% [+33.07, +39.68] | -0.13% [-3.67, +4.02] (indistinguishable) | R1: +22.92% [+17.88, +26.59] |
| G3 | 20 | 85648.2 | 109606 | +35.92% [+33.58, +41.09] | -0.43% [-4.21, +2.03] (indistinguishable) | R1: +22.44% [+17.72, +27.52] |
| G4 | 20 | 85375.6 | 112468 | +35.49% [+31.89, +37.61] | +2.17% [-3.87, +4.77] (indistinguishable) | R1: +22.05% [+17.07, +24.85] |
| G5 | 20 | 84945.6 | 109372 | +34.81% [+31.29, +38.92] | -0.65% [-4.44, +2.71] (indistinguishable) | R1: +21.44% [+16.18, +25.50] |

Raw samples: `measurement/raw_samples.jsonl` sha256 `cef73943453a11b46f1ec73dcef7ae2ea599fa881d57b755cd6098796a223384`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 15.47% > cap 5.0%; peak-memory overhead upper bound 5.52% > cap 5.0%
  - G1: latency overhead upper bound 38.26% > cap 5.0%
  - G2: latency overhead upper bound 39.68% > cap 5.0%
  - G3: latency overhead upper bound 41.09% > cap 5.0%
  - G4: latency overhead upper bound 37.61% > cap 5.0%
  - G5: latency overhead upper bound 38.92% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
  - G1: latency overhead upper bound 38.26% > cap 25.0%
  - G2: latency overhead upper bound 39.68% > cap 25.0%
  - G3: latency overhead upper bound 41.09% > cap 25.0%
  - G4: latency overhead upper bound 37.61% > cap 25.0%
  - G5: latency overhead upper bound 38.92% > cap 25.0%
