# PARAPET run — C1 (CWE-502 Deserialization of Untrusted Data)

- Generator used: True
- Commit: `5eefe0c1d143f2d71d014aadf8b696f6fb1b1a01` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3-C1-20261118T171545`

## Generation

| Candidate | Seed | Status | Wall s | Prompt tok | Completion tok | Finish | L1 | Extraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | 101 | success | 38.549 | 845 | 710 | stop | True | fenced code block #1 (java) declaring class PrefsCodec |
| G2 | 102 | success | 6.334 | 845 | 902 | stop | True | fenced code block #1 (java) declaring class PrefsCodec |
| G3 | 103 | success | 6.933 | 845 | 975 | stop | True | fenced code block #1 (java) declaring class PrefsCodec |
| G4 | 104 | success | 6.248 | 845 | 849 | stop | True | fenced code block #1 (java) declaring class PrefsCodec |
| G5 | 105 | success | 7.462 | 845 | 1058 | stop | True | fenced code block #1 (java) declaring class PrefsCodec |

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_legacy_linkedlist.b64 |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | probe_typical.b64, probe_empty.b64, probe_large.b64, probe_unicode.b64, probe_legacy_linkedlist.b64, probe_legacy_hashmap.b64 |
| G1 | generated candidate | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| G2 | generated candidate | FAIL | not run | not run | not run | not run | L1 | none |
| G3 | generated candidate | FAIL | not run | not run | not run | not run | L1 | none |
| G4 | generated candidate | FAIL | not run | not run | not run | not run | L1 | none |
| G5 | generated candidate | FAIL | not run | not run | not run | not run | L1 | none |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

A/A noise floor: latency 1.60%, peak memory 2.33%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 12676.4 | 103518 | — | — | — |
| baseline-AA | 20 | 12678.5 | 104180 | +0.02% [-1.60, +1.55] (indistinguishable) | +0.64% [-0.56, +2.33] (indistinguishable) | — |
| R1 | 20 | 12895.3 | 101524 | +1.73% [+0.51, +3.47] | -1.93% [-2.96, +0.50] (indistinguishable) | — |
| R2 | 20 | 4743.7 | 100832 | -62.58% [-63.61, -61.78] | -2.59% [-3.22, -1.31] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `05f759c3c0e5ad31ecd3f3afffa15374661b833fd486f0880f37ad52581ab975`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2', 'R1']; recommend R2.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
