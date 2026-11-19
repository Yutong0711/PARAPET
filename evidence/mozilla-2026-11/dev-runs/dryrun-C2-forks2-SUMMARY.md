# PARAPET run — C2 (CWE-611 Improper Restriction of XML External Entity Reference)

- Generator used: False
- Commit: `f9f9e15330af878f63347c18a73dad37404fa897` on `mozilla/local-slice`
- Work directory (Linux filesystem): `/home/yzhao/parapet-work/dev/cli-dryrun/dryrun-C2-20261118T170524`

## Validation

| Patch | Kind | Compile | Reproducer | Held-out 1 | Held-out 2 | Functional | Claim | Now rejects |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V0 | vulnerable (unpatched baseline) | ok | FAIL | FAIL | FAIL | pass | L2 | none |
| CONTROL | incomplete control patch (hand-written) | ok | pass | FAIL | FAIL | pass | L3 | none |
| R1 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | doctype_without_subset, internal_entity, internal_default_attribute, external_dtd_benign_local |
| R2 | reference fix (hand-written) | ok | pass | pass | pass | pass | L4 | external_dtd_benign_local |

## Measurement (ratio of medians vs unpatched baseline, 95% bootstrap CI)

| Arm | Valid forks | Median ns/op | Median peak RSS KiB | Latency overhead | Peak-memory overhead | vs matched ref (latency) |
| --- | --- | --- | --- | --- | --- | --- |
| baseline | 2 | 64564.4 | 111578 | — | — | — |
| baseline-AA | 2 | 66826.4 | 111114 | — | — | — |
| R1 | 2 | 70412.2 | 112818 | — | — | — |
| R2 | 2 | 64041.0 | 111940 | — | — | — |

Raw samples: `measurement/raw_samples.jsonl` sha256 `49bd96dded18c0f9de79f7262994a8e90965152ee14dacbaf54c36f85a20caf3`

## Decisions

- **strict** (caps {'latency_overhead_pct': 5.0, 'peak_memory_overhead_pct': 5.0}): fitting none; no admissible patch fits the strict budget; recommend none.
  - R1: no valid cost estimate
  - R2: no valid cost estimate
- **lenient** (caps {'latency_overhead_pct': 25.0, 'peak_memory_overhead_pct': 25.0}): fitting none; no admissible patch fits the lenient budget; recommend none.
  - R1: no valid cost estimate
  - R2: no valid cost estimate
