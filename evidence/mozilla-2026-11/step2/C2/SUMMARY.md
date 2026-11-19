# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: False
- Commit: `08900879fc58faef8b286e802179fef4522f831b` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step2-C2-20261118T171144`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 4.93%, peak memory 3.65%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 63080.0 | 112010 | — | — | — |
| baseline-AA | 20 | 63729.3 | 112256 | +1.03% [-4.93, +3.26] (indistinguishable) | +0.22% [-2.76, +3.65] (indistinguishable) | — |
| R1 | 20 | 69375.8 | 114776 | +9.98% [+4.25, +11.96] | +2.47% [-1.81, +5.09] (indistinguishable) | — |
| R2 | 20 | 63898.1 | 109692 | +1.30% [-3.75, +3.17] (indistinguishable) | -2.07% [-4.33, +3.36] (indistinguishable) | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `0e718a2a514b9fbe181937f9cef5895f677367385b1b210c73c44f7b2c81dc91`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 11.96% > cap 5.0%; peak-memory overhead upper bound 5.09% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
