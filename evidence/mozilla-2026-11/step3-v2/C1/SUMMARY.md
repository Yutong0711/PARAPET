# PARAPET run — C1 (CWE-502 Deserialization of Untrusted Data)

- Generator used: True
- Commit: `a137f02c4678bde5889045623cbff42e007829a2` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3v2-C1-20261118T174700`

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

A/A noise floor: latency 3.03%, peak memory 2.08%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 12650.6 | 104176 | — | — | — |
| baseline-AA | 20 | 12769.3 | 103562 | +0.94% [-1.20, +3.03] (indistinguishable) | -0.59% [-2.08, +0.46] (indistinguishable) | — |
| R1 | 20 | 13063.3 | 102582 | +3.26% [+2.21, +4.47] | -1.53% [-4.40, -0.06] (indistinguishable) | — |
| R2 | 20 | 4668.8 | 76720 | -63.09% [-63.60, -62.39] | -26.36% [-27.97, -25.17] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `983498a69b4661465f9088f50abcf8030fb7d994b7c7f6f9a64ba29decd7e9c9`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2', 'R1']; recommend R2.
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
