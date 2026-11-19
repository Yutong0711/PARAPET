# PARAPET run — L1 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: False
- Commit: `083b7b8a66debb9ab80f556cb44419bf918a4ef6` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step4-L1-20261118T181230`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | upstream fix (commit e6fddca, three files) | ok | pass | pass | pass | pass | L4 | none |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 5.77%, peak memory 5.86%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 56426.0 | 100850 | — | — | — |
| baseline-AA | 20 | 55697.3 | 99684 | -1.29% [-5.77, +3.93] (indistinguishable) | -1.16% [-5.86, +5.47] (indistinguishable) | — |
| R1 | 20 | 78306.0 | 105964 | +38.78% [+33.34, +45.92] | +5.07% [+0.53, +10.63] (indistinguishable) | — |
| R2 | 20 | 62336.5 | 106052 | +10.47% [+4.42, +15.44] | +5.16% [+1.24, +10.33] (indistinguishable) | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `3c730c9367cb7982f43fafb443aaa63dabecd3b6be5a4b40662aee11e05a8d34`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting none; no admissible patch fits the strict budget; recommend none.
  - R1: latency overhead upper bound 45.92% > cap 5.0%; peak-memory overhead upper bound 10.63% > cap 5.0%
  - R2: latency overhead upper bound 15.44% > cap 5.0%; peak-memory overhead upper bound 10.33% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 45.92% > cap 25.0%
