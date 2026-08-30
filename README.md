# PARAPET

[![CI](https://github.com/Yutong0711/PARAPET/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Yutong0711/PARAPET/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0-informational.svg)](VERSION)

**PARAPET v1.0** — the public integration baseline for the PARAPET platform and
its six founding research artifacts. The version of record is in
[`VERSION`](VERSION); changes are listed in [`CHANGELOG.md`](CHANGELOG.md).

**PARAPET** turns a security exposure into a reviewable decision. Almost all
commercial software now depends on open-source components, and most of those
components carry a known vulnerability. Fixing one has a price — added latency,
memory, or CPU — and a project with paid engineers and a benchmarking harness
can measure that price and decide. A library with two volunteers and a thousand
dependents cannot, so the fix that matters most waits at a contributor who has
no way to weigh it.

PARAPET is a language-model pipeline that closes that gap. For one exposure at a
time it identifies the weakness and its reproducer, drafts more than one way to
remove it, measures each candidate on the project's own workloads, and checks
the result against a **service budget** the maintainer declared in advance — a
written limit on how much runtime cost security may add. What reaches the
maintainer is a **hardening record**: what was removed, the check that proves
it, what it cost, and how to reproduce both. That is the platform's end-to-end
design.

**This repository is PARAPET v1.0: the public technical baseline for that
design.** It establishes the founding component stack — six research artifacts
under one release — together with the component-level capabilities that are
executable today, the release infrastructure, the automated validation, and the
public website. PESOSE Track 1 builds on this baseline: it integrates and
hardens those capabilities into a single maintainer-facing exposure-to-decision
workflow, and it scopes how PARAPET becomes a governed open-source ecosystem.
The sections below separate what runs here from what Track 1 adds.

## The unified story

The hardening loop has three jobs, and each founding artifact owns part of one:

1. **Draft** a fix that closes the weakness — **CoQuIR** retrieves the secure
   coding pattern (its `SaferCode` and `CVEFixes` preference-retrieval tasks are
   the security subset), and **More Than Just Functional** contributes the
   multi-candidate generate-and-critique workflow.
2. **Measure** what each candidate costs — **PerfOrch** generates the
   candidates, compiles and runs them across languages, and records execution
   time and memory on real benchmarks; **Metior** supplies the statistics that
   make those numbers trustworthy under noise: dependent-data bootstrapping, a
   stopping rule fixed before the run, tail-aware reporting.
3. **Guard** the pipeline itself — **LUNA** compares the agent's observed
   behavior against a pinned reference profile to catch a degraded or
   compromised model, and **PrivAuditor** is the data-protection review that
   must clear any model adaptation before it is used.

PerfOrch is the seed tool that already runs the middle job. CoQuIR is the core
security artifact; LUNA and PrivAuditor are supporting security controls; Metior
supplies the measurement statistics; More Than Just Functional is background
evidence for the drafting workflow. **PARAPET v1.0 is the baseline that carries
these components and their provenance, licensing, and validation.** The
integrated workflow that binds the three jobs into one maintainer-facing loop —
along with the threat model, the security policy, repository ingestion, and
pull-request integration — is the Track 1 work built on top of that baseline,
and is scoped rather than shipped here.

## Repository layout

```
projects/
  perforch/                   README.md + src/   seed: LLM candidate generation + runtime measurement
  coquir/                     README.md + src/   core: security-aware code retrieval (SaferCode, CVEFixes)
  metior/                     README.md + src/   measurement statistics under noise (dependent-data bootstrapping)
  luna/                       README.md + src/   reference-profile monitoring of agent/model behavior
  privauditor/                README.md + src/   data-protection review for model adaptation
  more-than-just-functional/  README.md + src/   background: multi-candidate generation + critique
index.html, styles.css, script.js   the PARAPET website (GitHub Pages)
tests/                              PARAPET's automated test suite
scripts/run_tests.sh                one command to run the supported checks
.github/workflows/                  CI, GitHub Pages deployment, release validation
VERSION                             PARAPET's release version (1.0)
THIRD_PARTY_NOTICES.md              vendored components and the licenses they carry
```

Each project folder is a **vendored snapshot**: source under `src/`, the
project's own `README.md` (with a provenance banner), and the project-level
license or license statement that applies to that folder. All six carry one.
Derived results, evaluation dumps, datasets, virtualenvs, and duplicate document
formats were removed to keep this repository lightweight — each folder README
points back to the full upstream material.

| Project | Origin | Paper | Role |
| --- | --- | --- | --- |
| PerfOrch | [qzydustin/perforch](https://github.com/qzydustin/perforch) `e873cd9` | — | Seed pipeline |
| CoQuIR | Derui Zhu artifact bundle v1.0 | ACL 2026 | Core |
| Metior | ASE 2021 research artifact (He et al.) | ASE 2021 | Supporting |
| LUNA | Derui Zhu artifact bundle v1.0 | IEEE TSE 2024 | Supporting |
| PrivAuditor | Derui Zhu artifact bundle v1.0 | NeurIPS 2024 D&B | Supporting |
| More Than Just Functional | Derui Zhu artifact bundle v1.0 | NeurIPS 2025 | Background |

## What is in this release

**PARAPET v1.0 is the public integration baseline** for the platform and for the
Track 1 work. It packages:

- the six founding research artifacts listed above, each with a provenance
  banner and the project-level license that applies to it;
- the component-level capabilities that are executable today — chiefly
  PerfOrch's candidate generation, cross-language compile-and-run, and runtime
  measurement, plus the More Than Just Functional profiler transform — together
  with the tests that exercise them;
- the PARAPET project website served from GitHub Pages;
- the release infrastructure: `VERSION`, [`CHANGELOG.md`](CHANGELOG.md), the
  licensing and provenance record, the automated test suite, and CI/CD.

Track 1 builds on this baseline. It integrates and hardens these capabilities
into a single maintainer-facing exposure-to-decision workflow, and adds the
mechanisms that workflow needs: stronger orchestration across the components,
repository ingestion, pull-request integration, the service-budget and
hardening-record objects, governance, and ecosystem validation. Those are
scoped in "What Track 1 scopes" below; they are not all implemented here.

What runs today is bounded by what the test suite covers — see "Running the
tests" for exactly which components CI exercises, and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the ones that cannot yet be run from a
clean clone and what each would require.

## Running the tests

The repository ships a test suite covering the parts of the vendored snapshots
that are self-contained enough to run from a clean clone, plus structural checks
on provenance, licensing, versioning, and the website.

```bash
python3 -m pip install -r requirements-dev.txt
./scripts/run_tests.sh
```

`scripts/run_tests.sh` is a transparent wrapper around the same `pytest`
commands CI runs; individual suites can be run with `functional`, `jvm`, or
`sanity` as an argument. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for what each
suite covers, and for the components that cannot be tested here.

**What CI does and does not validate.** CI exercises PerfOrch's deterministic
core — function extraction and benchmark assembly across all five languages,
prompt construction, the model-selection memory, benchmark loading, and the
per-language benchmark-loop transformations — and runs generated candidates
end-to-end through its Python and Java backends, compiling and executing them.
It also exercises the More Than Just Functional AST profiler transform.

CI does **not** functionally test CoQuIR, LUNA, PrivAuditor, or Metior, and
does not compile or run anything through the Go, Rust, or C++ backends: those
need retrieval models, GPUs, datasets removed from these snapshots, or
toolchains out of scope for a hosted runner. [`CONTRIBUTING.md`](CONTRIBUTING.md)
lists each one and exactly what running it would require.

## What Track 1 scopes

- **Ecosystem discovery (PA1):** quota-sampled maintainer interviews, repository
  mining of how often hardening is reverted or reopened citing runtime cost, and
  three pilot integrations scored by an independent evaluator.
- **Organization and governance (PA2):** who holds authority over a declared
  service budget, who owns the non-code assets (benchmark workloads, pattern
  catalog, tuned weights), and what pays for the ecosystem. The core license is
  settled — Apache-2.0 — so what PA2 studies is the governance built around it:
  a contributor agreement weighed against a DCO, and how the ecosystem
  interoperates with components that carry other licenses.
- **Risk analysis and security plan (PA3):** a threat model for the six risk
  classes in the initial register — gamed measurement, one fix opening another,
  a quietly changed budget, a compromised agent model, capture of budget or
  evaluation authority, and standing supply-chain risks — each mapped to a
  control. The measurement is the newest thing to trust and the cheapest to
  attack.
- **Community building (PA4):** user and contributor funnels on CHAOSS metrics,
  a workshop and a mentored sprint, and course modules across three campuses,
  two of them Hispanic-Serving Institutions.

## Team

Led by California State University, Long Beach (PI Yutong Zhao), with the
Rochester Institute of Technology (Co-PI Derui Zhu) and the University of Arizona
(Co-PIs Sen He and Bo Liu).

## License

PARAPET uses a layered licensing model, and the boundary between the root
project, the project-level snapshots, and the third-party components nested
inside them matters.

**PARAPET-owned root repository content is licensed under the
[Apache License 2.0](LICENSE).** That covers the website (`index.html`,
`styles.css`, `script.js`), this README and the other root documentation, the
test suite under `tests/`, `scripts/`, and the GitHub Actions workflows.

**Each top-level directory under `projects/` carries its own project-level
license and provenance.** The root Apache-2.0 grant does not reach into
`projects/` on its own.

- **PerfOrch**, **LUNA**, and **More Than Just Functional** are project-level
  snapshots controlled by the project team, which holds the authority to
  license them. The team has released their *project-level* content under the
  Apache License 2.0, and each directory carries its own `LICENSE` file.
- **CoQuIR**, **Metior**, and **PrivAuditor** retain the licenses supplied with
  them.
- **Third-party components nested inside any of those directories retain their
  own licenses.** Neither the root nor the project-level Apache-2.0 grant
  relicenses them: hmmlearn under `projects/luna/` stays BSD-3-Clause, and the
  PEFT fork and MIMIR under `projects/privauditor/` stay Apache-2.0 and MIT.

| Component | License as checked in | License file |
| --- | --- | --- |
| PerfOrch | Apache-2.0 (project-team decision) | `projects/perforch/LICENSE` |
| CoQuIR | Apache-2.0 | `projects/coquir/LICENSE` |
| Metior | BSD License 2.0 (statement only) | `projects/metior/LICENSE.md` |
| LUNA | Apache-2.0 (project-team decision) for project-level content; bundled hmmlearn stays BSD-3-Clause | `projects/luna/LICENSE` |
| PrivAuditor | Apache-2.0; datasets under ODC-By; nested PEFT Apache-2.0, MIMIR MIT | `projects/privauditor/LICENSE` |
| More Than Just Functional | Apache-2.0 (project-team decision) | `projects/more-than-just-functional/LICENSE` |

**Before using or redistributing any component, read the license and provenance
files inside that component's directory.** The full record — every preserved
license file, every nested third-party component, and the known gaps — is in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
