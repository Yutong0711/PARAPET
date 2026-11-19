# PARAPET run — C1 (CWE-502 Deserialization of Untrusted Data)

- Generator used: False
- Commit: `a137f02c4678bde5889045623cbff42e007829a2` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step2v2-C1-20261118T174128`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_legacy_linkedlist.b64 |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 2.27%, peak memory 1.91%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 12683.4 | 104156 | — | — | — |
| baseline-AA | 20 | 12585.4 | 103264 | -0.77% [-2.27, +1.01] (indistinguishable) | -0.86% [-1.91, +0.48] (indistinguishable) | — |
| R1 | 20 | 13005.5 | 102658 | +2.54% [+0.74, +3.78] | -1.44% [-4.04, +0.30] (indistinguishable) | — |
| R2 | 20 | 4635.9 | 76198 | -63.45% [-64.02, -63.09] | -26.84% [-27.31, -25.09] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `a1c147bdf667a3679670b6481da7e6764d43bfb4e552180a6338a9eb979719be`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2', 'R1']; recommend R2.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
