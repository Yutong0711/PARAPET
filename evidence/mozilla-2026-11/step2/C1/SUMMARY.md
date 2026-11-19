# PARAPET run — C1 (CWE-502 Deserialization of Untrusted Data)

- Generator used: False
- Commit: `08900879fc58faef8b286e802179fef4522f831b` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step2-C1-20261118T170907`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_legacy_linkedlist.b64 |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 1.23%, peak memory 1.81%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 12634.0 | 103786 | — | — | — |
| baseline-AA | 20 | 12661.1 | 104232 | +0.21% [-1.23, +1.18] (indistinguishable) | +0.43% [-1.02, +1.81] (indistinguishable) | — |
| R1 | 20 | 12979.2 | 102206 | +2.73% [+0.86, +4.24] | -1.52% [-4.32, +1.17] (indistinguishable) | — |
| R2 | 20 | 4682.5 | 76134 | -62.94% [-63.55, -62.13] | -26.64% [-27.41, -25.44] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `fa10b25430acf50639751e2b6132199345665e05adffb0f35f8791e08a790362`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2', 'R1']; recommend R2.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
