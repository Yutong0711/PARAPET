# PARAPET run — L1 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: True
- Commit: `2ac56563e219ecf72c31ee33d8c4dd262d97d0f5` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step4gen-frozen-L1-20261118T181605`

## Generation

| Candidate | Seed | Status | Wall s | Prompt tok | Completion tok | Finish | L1 | Extraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | success | 19.687 | 4098 | 2048 | stop | False | 1 fenced block(s), none declares class BaseXMLBuilder |
| G2 | 102 | success | 3.368 | 4098 | 464 | stop | False | no fenced code block and no class BaseXMLBuilder declaration |
| G3 | 103 | success | 1.221 | 4098 | 164 | stop | False | no fenced code block and no class BaseXMLBuilder declaration |
| G4 | 104 | success | 3.843 | 4098 | 528 | stop | False | no fenced code block and no class BaseXMLBuilder declaration |
| G5 | 105 | success | 4.029 | 4098 | 559 | stop | False | no fenced code block and no class BaseXMLBuilder declaration |

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | upstream fix (commit e6fddca, three files) | ok | pass | pass | pass | pass | L4 | none |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 1.82%, peak memory 4.40%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 55154.9 | 98690 | — | — | — |
| baseline-AA | 20 | 55202.3 | 98940 | +0.09% [-1.82, +1.45] (indistinguishable) | +0.25% [-3.89, +4.40] (indistinguishable) | — |
| R1 | 20 | 77695.3 | 106070 | +40.87% [+37.96, +42.79] | +7.48% [+4.10, +10.01] | — |
| R2 | 20 | 61436.8 | 105810 | +11.39% [+9.08, +13.10] | +7.21% [+3.83, +9.94] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `99eb1532337a5e1ffb3998c776c199d2e03c5472cc872cda9529b0adc365cd4e`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting none; no admissible patch fits the strict budget; recommend none.
  - R1: latency overhead upper bound 42.79% > cap 5.0%; peak-memory overhead upper bound 10.01% > cap 5.0%
  - R2: latency overhead upper bound 13.10% > cap 5.0%; peak-memory overhead upper bound 9.94% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 42.79% > cap 25.0%
