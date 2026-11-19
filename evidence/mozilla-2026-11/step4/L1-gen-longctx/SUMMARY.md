# PARAPET run — L1 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: True
- Commit: `2ac56563e219ecf72c31ee33d8c4dd262d97d0f5` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step4gen-longctx-remeasure-L1-20261118T183019`

## Generation

| Candidate | Seed | Status | Wall s | Prompt tok | Completion tok | Finish | L1 | Extraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | success | 87.731 | 10075 | 9934 | stop | True | fenced code block #1 (java) declaring class BaseXMLBuilder |
| G2 | 102 | success | 80.726 | 10075 | 10112 | stop | True | fenced code block #1 (java) declaring class BaseXMLBuilder |
| G3 | 103 | success | 81.804 | 10075 | 10128 | stop | True | fenced code block #1 (java) declaring class BaseXMLBuilder |
| G4 | 104 | success | 80.252 | 10075 | 9935 | stop | True | fenced code block #1 (java) declaring class BaseXMLBuilder |
| G5 | 105 | success | 80.003 | 10075 | 10128 | stop | True | fenced code block #1 (java) declaring class BaseXMLBuilder |

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | upstream fix (commit e6fddca, three files) | ok | pass | pass | pass | pass | L4 | none |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G1 | generated candidate | ok | FAIL | FAIL | FAIL | FAIL | L2 | none |
| G2 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G3 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| G4 | generated candidate | ok | FAIL | FAIL | FAIL | FAIL | L2 | none |
| G5 | generated candidate | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 2.93%, peak memory 6.22%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 54636.9 | 97366 | — | — | — |
| baseline-AA | 20 | 55341.1 | 99524 | +1.29% [-1.08, +2.93] (indistinguishable) | +2.22% [-3.50, +6.22] (indistinguishable) | — |
| R1 | 20 | 76770.4 | 108082 | +40.51% [+37.56, +42.77] | +11.01% [+5.13, +14.07] | — |
| R2 | 20 | 60720.4 | 105000 | +11.13% [+8.89, +12.89] | +7.84% [+2.46, +10.01] | — |
| G2 | 20 | 99134.4 | 108100 | +81.44% [+77.61, +85.58] | +11.02% [+5.53, +12.26] | R2: +63.26% [+60.37, +66.96] |
| G3 | 20 | 99322.9 | 107586 | +81.79% [+77.82, +84.91] | +10.50% [+5.05, +11.97] | R2: +63.57% [+60.89, +66.13] |
| G5 | 20 | 100326.6 | 108630 | +83.62% [+79.61, +89.75] | +11.57% [+6.27, +12.81] | R2: +65.23% [+62.41, +70.64] |

Raw samples: `measurement/raw_samples.jsonl` sha256 `5aefdc587cb04548c484fd7c287923a71f6a8051eda296db87e3833f30aaaf31`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting none; no admissible patch fits the strict budget; recommend none.
  - R1: latency overhead upper bound 42.77% > cap 5.0%; peak-memory overhead upper bound 14.07% > cap 5.0%
  - R2: latency overhead upper bound 12.89% > cap 5.0%; peak-memory overhead upper bound 10.01% > cap 5.0%
  - G2: latency overhead upper bound 85.58% > cap 5.0%; peak-memory overhead upper bound 12.26% > cap 5.0%
  - G3: latency overhead upper bound 84.91% > cap 5.0%; peak-memory overhead upper bound 11.97% > cap 5.0%
  - G5: latency overhead upper bound 89.75% > cap 5.0%; peak-memory overhead upper bound 12.81% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 42.77% > cap 25.0%
  - G2: latency overhead upper bound 85.58% > cap 25.0%
  - G3: latency overhead upper bound 84.91% > cap 25.0%
  - G5: latency overhead upper bound 89.75% > cap 25.0%
