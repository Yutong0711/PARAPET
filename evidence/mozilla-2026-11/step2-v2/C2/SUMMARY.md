# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: False
- Commit: `a137f02c4678bde5889045623cbff42e007829a2` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step2v2-C2-20261118T174352`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 2.72%, peak memory 3.55%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 63067.5 | 111730 | — | — | — |
| baseline-AA | 20 | 63552.4 | 110992 | +0.77% [-2.05, +2.72] (indistinguishable) | -0.66% [-3.55, +2.68] (indistinguishable) | — |
| R1 | 20 | 69131.5 | 112334 | +9.62% [+7.06, +11.48] | +0.54% [-2.74, +4.45] (indistinguishable) | — |
| R2 | 20 | 64329.2 | 111280 | +2.00% [-0.64, +5.08] (indistinguishable) | -0.40% [-2.18, +4.68] (indistinguishable) | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `4866dacfa3f1cd52ac8c20c978630f20b7caef291910699eadac08bfcecac798`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting none; no admissible patch fits the strict budget; recommend none.
  - R1: latency overhead upper bound 11.48% > cap 5.0%
  - R2: latency overhead upper bound 5.08% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
