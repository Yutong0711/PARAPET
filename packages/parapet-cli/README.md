# parapet

The one command that produces a hardening record.

```bash
pip install parapet
parapet init                       # write a service budget, then edit it
parapet run --repo . --commit HEAD \
    --issues issues.csv \
    --before before.csv --after after.csv --source src/main/java \
    --changed-methods acme.Loader#load \
    --budget parapet-budget.yaml --out records/
parapet show records/HEAD.json
```

Installing `parapet` pulls in the four components. Each also installs and
runs on its own; see the top-level [README](../../README.md).

## What comes out

```
record a1b2c3d4  [unscored]
  exposure: 1841 (performance, no CWE)
    Importing a 200 MB dump takes most of the time
    reproducer: none recorded
    matched: spend_time, memory, duration
  review cost: design-level, Change Propagation (Type-I)
    8 production file(s), 2 test file(s)
    tests: Test Case Addition, Method Replacement
  cost: latency 12900ms (baseline 12400, no interval) on bench/read-throughput
  the cost landed: below
    Expensive Callee: Loader#load spends 92% of its time below it
  warning: at least one cost has no interval, so the budget decision cannot be made
```

## Every stage is optional

Run with only `--issues` and you get triage. Add `--repo` and you get
review cost. Add profiles and a graph and you get measured cost and
attribution. Add `--budget` and you get a verdict.

A stage that could not run says so. `parapet run` prints which stages ran
and which were skipped and why, because a record that silently omits a
check looks exactly like one that passed it.

## The verdict

`admitted`, `overrun`, or `unscored`.

`unscored` is the common one at first, and it is the tool refusing to
launder a guess into a decision. A cost measured once has no confidence
interval, and a change is admitted only when the whole interval fits the
budget. Measure several times and set the interval.

For CI:

```bash
parapet run ... --fail-on-overrun        # exit 2 when the cost exceeds the budget
parapet run ... --fail-unless-admitted   # exit 3 unless the record is clean
```

The second is stricter and is what to use if you do not want `unscored`
passing quietly.

## The service budget

`parapet init` writes a commented starter. Two fields decide whether it is
worth anything:

- **`authority`**: who may change these limits, and on what evidence. A
  budget without one is rejected at load. Whoever can edit the file
  decides how much security the project buys.
- **`workloads`**: what a cost claim is measured on. "5% slower" means
  nothing until someone says at what.

## Diagnostics

```bash
parapet doctor
parapet doctor --budget parapet-budget.yaml
```

Lists what is installed, what each stage needs, and what a budget file
actually allows.

Apache-2.0.
