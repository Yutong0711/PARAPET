# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: True
- Commit: `8c8ad50572f6188171600b7899de488b9725ecfc` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3v3-C2-20261118T190755`

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

A/A noise floor: latency 3.23%, peak memory 4.56%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 61235.5 | 112286 | — | — | — |
| baseline-AA | 20 | 61734.8 | 112614 | +0.82% [-0.07, +3.23] (indistinguishable) | +0.29% [-2.04, +4.56] (indistinguishable) | — |
| R1 | 20 | 67062.2 | 110560 | +9.52% [+8.43, +11.29] | -1.54% [-2.91, +1.03] (indistinguishable) | — |
| R2 | 20 | 62124.6 | 112966 | +1.45% [+0.67, +3.54] (indistinguishable) | +0.61% [-1.10, +4.20] (indistinguishable) | — |
| G1 | 20 | 81461.7 | 108408 | +33.03% [+31.42, +35.07] | -3.45% [-5.85, +0.31] (indistinguishable) | R1: +21.47% [+19.79, +22.84] |
| G2 | 20 | 81723.1 | 110388 | +33.46% [+31.37, +36.25] | -1.69% [-3.79, +3.64] (indistinguishable) | R1: +21.86% [+19.72, +23.85] |
| G3 | 20 | 81942.1 | 108948 | +33.81% [+32.12, +36.39] | -2.97% [-5.21, +0.91] (indistinguishable) | R1: +22.19% [+20.38, +24.17] |
| G4 | 20 | 82017.6 | 109624 | +33.94% [+32.53, +36.10] | -2.37% [-4.01, +0.61] (indistinguishable) | R1: +22.30% [+20.72, +23.80] |
| G5 | 20 | 80799.3 | 110004 | +31.95% [+31.07, +34.23] | -2.03% [-4.00, +3.69] (indistinguishable) | R1: +20.48% [+19.32, +22.27] |

Raw samples: `measurement/raw_samples.jsonl` sha256 `de31fb8ecfe799b6c97076a8ed71edf260d8c908abf70b5eedb14ae25af164a6`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 11.29% > cap 5.0%
  - G1: latency overhead upper bound 35.07% > cap 5.0%
  - G2: latency overhead upper bound 36.25% > cap 5.0%
  - G3: latency overhead upper bound 36.39% > cap 5.0%
  - G4: latency overhead upper bound 36.10% > cap 5.0%
  - G5: latency overhead upper bound 34.23% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
  - G1: latency overhead upper bound 35.07% > cap 25.0%
  - G2: latency overhead upper bound 36.25% > cap 25.0%
  - G3: latency overhead upper bound 36.39% > cap 25.0%
  - G4: latency overhead upper bound 36.10% > cap 25.0%
  - G5: latency overhead upper bound 34.23% > cap 25.0%
