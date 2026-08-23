# PARAPET

Turn a security or performance exposure into a reviewable decision.

Hardening running code costs something, and almost no volunteer-run
project can say how much. Mozilla measured the cost of sandboxing a font
library, found the effect on real page loads acceptable, and shipped. The
Linux kernel measured its CPU mitigations, found the cost uneven across
workloads, and now ships a documented switch that turns them off. Both had
paid engineers, representative workloads and a benchmarking harness. A
library with two maintainers and a thousand dependent packages has none of
that, so hardening there waits, or merges with its cost unknown.

PARAPET answers the question that stalls it: **what does this change cost,
and does that fit what the project already said it would pay?**

What comes out is a *hardening record*: what the change is about, how wide
it is and how to review it, what it cost, where in the architecture that
cost landed, and whether it fits the budget the project declared in
advance.

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

## The pieces

Four packages. Each installs and runs on its own; `parapet` chains them.

| Package | Question it answers | Needs |
| --- | --- | --- |
| [`parapet-triage`](packages/parapet-triage) | Is this report about the kind of problem I am looking for, and why? | an issue export, a CSV, or an OSV advisory |
| [`parapet-scope`](packages/parapet-scope) | How wide is this change, and where should a reviewer start? | a git checkout with Java sources |
| [`parapet-attrib`](packages/parapet-attrib) | The benchmark says 4% slower. Where did the 4% go? | two profiles and a call graph |
| [`parapet-record`](packages/parapet-record) | The shared schema, and the budget check | nothing |

Install only what you need:

```bash
pip install parapet-triage      # triage alone, no other dependency but PyYAML
pip install parapet-scope       # scope alone, zero dependencies
pip install parapet-attrib      # attribution alone, zero dependencies
```

## Three things worth knowing before you try it

**It explains itself.** Every triage verdict names the patterns that
produced it. Every scope verdict names the structural evidence. Every
attribution says which methods carry the added cost. A tool whose output
feeds a security review has to be checkable in a few seconds, and an
opaque score is not.

**It refuses to decide when it cannot.** A cost measured once has no
confidence interval, so the record comes back `unscored` rather than
`admitted`. A budget that declares no limit for a dimension does not pass
that dimension, it declines to judge it. This is deliberate: a record that
silently omits a check looks exactly like one that passed it.

**It installs in minutes, not hours.** No compiler, no commercial
analyser, no model download. `parapet-scope` reads Java structure from
source text, `parapet-attrib` builds a call graph the same way, and
`parapet-triage` classifies with pattern matching that needs no training
corpus. Each of those choices costs accuracy in a documented way, and each
package says where.

## The service budget

The budget is the piece that makes the rest useful. It is a small file a
maintainer writes once:

```yaml
project: acme
authority: >-
  Changes require review by two maintainers and a note explaining what
  workload evidence justified the new limit.
limits:
  latency: "5%"
  memory: "10%"
binding: [latency]
workloads:
  - "bench/read-throughput"
```

Whoever can edit that file decides how much security the project buys.
Lowering a limit quietly is the attack: hardening the project would
otherwise accept starts failing its own check, the defences weaken, and no
security code changed for a reviewer to see. Review changes to it the way
you review a change to a signing key.

## Documentation

- [Quickstart](docs/quickstart.md), the under-an-hour path
- [Installing](docs/install.md)
- [The record schema](docs/record-schema.md)
- [Java setup](docs/java-setup.md): call graphs and profiles
- [Writing your own pattern set](docs/pattern-sets.md)
- [Troubleshooting](docs/troubleshooting.md)

## Provenance

The three analysis components implement methods from peer-reviewed work,
and each package keeps the validation under `paper/`:

- Triage implements the heuristic linguistic pattern framework of Zhao,
  Xiao and Wong, *IEEE TSE* 50(7), 2024
  ([10.1109/TSE.2024.3390623](https://doi.org/10.1109/TSE.2024.3390623)).
  The 80 published patterns ship with the package.
- Scope implements the change-scope and design-level pattern taxonomy of
  Zhao, Xiao, Bondi, Chen and Liu, *IEEE TSE* 49(2), 2023
  ([10.1109/TSE.2022.3167628](https://doi.org/10.1109/TSE.2022.3167628)),
  derived from 570 hand-coded issues.
- Attribution implements the architectural cost attribution of Zhao, Xiao,
  Wang, Chen, Chen and Liu, *IEEE ICSA* 2020
  ([10.1109/ICSA47634.2020.00027](https://doi.org/10.1109/ICSA47634.2020.00027)).

`CITATION.cff` has the full entries. The bundled pattern sets and code
books carry CC BY 4.0 attribution in [`NOTICE`](NOTICE).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) first, and
[SECURITY.md](SECURITY.md) before reporting anything that looks like a
vulnerability. Governance is at an early stage and is written down in
[GOVERNANCE.md](GOVERNANCE.md), including who may change what.

Apache-2.0. See [LICENSE](LICENSE).
