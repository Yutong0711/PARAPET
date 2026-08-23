# The hardening record

One document per proposed change, answering four questions: what it
removes, the check that proves it, what it cost, and how to reproduce
both.

Each component fills part of it, and the parts compose because they share
this schema.

## Fields

```jsonc
{
  "schema_version": "1.0.0",
  "record_id": "AVRO-753",
  "change_ref": "a1b2c3d4e5f6...",

  "exposure": {                     // parapet-triage
    "identifier": "GHSA-abcd-1234",
    "kind": "security",             // security | performance | unknown
    "cwe": "CWE-122",
    "title": "Heap overflow in the decoder",
    "text": "...",
    "reproducer": "oss-fuzz testcase 4821",
    "source": "advisories/GHSA-abcd-1234.json",
    "labels": ["memory_safety", "reproducer_present"],
    "confidence": 0.94
  },

  "budget": {                       // the project's declared limits
    "project": "acme",
    "version": "1",
    "limits": {"latency": "5%", "memory": "64mb"},
    "binding": ["latency"],
    "workloads": ["bench/read-throughput"],
    "authority": "two maintainers, with workload evidence"
  },

  "costs": [                        // parapet-attrib
    {
      "dimension": "latency",       // latency | memory | cpu
      "value": 12900.0,
      "unit": "ms",
      "interval_low": 12820.0,
      "interval_high": 12980.0,
      "baseline": 12400.0,
      "workload": "bench/read-throughput",
      "n_samples": 5,
      "settled": true
    }
  ],

  "budget_checks": [
    {
      "dimension": "latency",
      "limit": "5%",
      "measured": 12900.0,
      "unit": "ms",
      "fits": true,
      "interval_fits": true,
      "overrun": 0.0,
      "reason": "relative to the recorded baseline"
    }
  ],

  "review_cost": {                  // parapet-scope
    "n_production_files": 8,
    "n_test_files": 2,
    "scope": "design-level",
    "design_pattern": "Change Propagation (Type-I)",
    "cochange_patterns": ["Test Case Addition", "Method Replacement"],
    "added_dependencies": 12,
    "removed_dependencies": 1,
    "added_files": ["src/main/java/acme/EncoderFactory.java"],
    "removed_files": []
  },

  "attribution": {                  // parapet-attrib
    "where": "below",
    "contained": 0.91,
    "in_changed_methods": 40.0,
    "in_callees": 430.0,
    "in_callers": 12.0,
    "outside_space": 18.0,
    "patterns": [{"pattern": "Expensive Callee", "...": "..."}]
  },

  "verdict": "admitted",            // admitted | overrun | unscored

  "components": [
    {
      "component": "parapet-attrib",
      "provenance": {
        "tool": "parapet-attrib",
        "tool_version": "0.1.0",
        "schema_version": "1.0.0",
        "created_at": "2026-08-22T18:04:00+00:00",
        "inputs": {"before_profile": "sha256:...", "after_profile": "sha256:..."},
        "environment": {"python": "3.12.3", "platform": "...", "java": "..."},
        "command": "parapet-attrib diff --before ..."
      },
      "payload": {}
    }
  ],

  "warnings": []
}
```

## Three rules the schema enforces rather than documents

**A limit carries its unit.** `"5%"`, `"1.2x"`, `"20ms"`, `"64mb"`.
Comparing a measurement against a limit in a different unit raises
`BudgetError` instead of returning a wrong answer.

**A change is admitted only when the whole interval fits.** A measurement
with no interval leaves the record `unscored`. One sample is not a
distribution, and a record that said `admitted` on one sample would look
exactly like one that earned it.

**A dimension the budget does not declare is a non-decision.** The check
records `fits: true` with `interval_fits: null` and a reason saying the
budget cannot decide. It is not a pass.

## Why provenance is in every record

The record is what a maintainer decides on, so bending it moves a bad
change through review without touching the code. Three things make a
changed input visible to anyone who re-runs: every input is hashed, the
environment is recorded, and the command line is kept. None stops a
determined attacker alone. Together they mean a record that was produced
differently cannot claim it was not.

See [SECURITY.md](../SECURITY.md) for the threat model this comes from.

## Versioning

The major version is a compatibility boundary. `load_record` refuses a
record whose major version differs from the reader's, rather than reading
it partially and producing a decision that looks valid.

Adding an optional field is a minor version. Changing the meaning of an
existing field, or making an optional field required, is a major version
of every package.

## Working without `parapet-record`

Each component writes the same fields as plain JSON when
`parapet-record` is not installed, so a minimal install is never blocked.
Those records carry a warning saying they have no input hashes and no
environment profile, which is to say they are not verifiable. Install
`parapet-record` for anything you intend to rely on.
