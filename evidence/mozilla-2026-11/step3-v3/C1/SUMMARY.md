# PARAPET run — C1 (CWE-502 Deserialization of Untrusted Data)

- Generator used: True
- Commit: `8c8ad50572f6188171600b7899de488b9725ecfc` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/runs/step3v3-C1-20261118T190532`

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

A/A noise floor: latency 3.99%, peak memory 1.75%.

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 20 | 12040.3 | 103560 | — | — | — |
| baseline-AA | 20 | 12229.7 | 103408 | +1.57% [-0.74, +3.99] (indistinguishable) | -0.15% [-1.75, +1.29] (indistinguishable) | — |
| R1 | 20 | 12565.8 | 101932 | +4.37% [+1.97, +5.77] | -1.57% [-4.12, -0.14] (indistinguishable) | — |
| R2 | 20 | 4442.2 | 76642 | -63.11% [-63.87, -62.54] | -25.99% [-26.62, -24.64] | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `da6acbee5dbb351af25269cabd6c2ebbe449be0ea14caa648ed2bb6e1c20fcb4`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting ['R2']; recommend R2.
  - R1: latency overhead upper bound 5.77% > cap 5.0%
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting ['R2', 'R1']; recommend R2.
