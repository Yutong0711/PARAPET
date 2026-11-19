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

## PARAPET 1.1.0-alpha: a working prototype of the hardening workflow (unreleased)

PARAPET makes security hardening a performance-budgeted decision. The
`mozilla/local-slice` branch adds [`parapet/`](parapet/), the first
implementation of the workflow itself (Apache-2.0, Python). It is a working
prototype. For one known weakness it runs four stages:

- **Generate** candidate fixes with a local open-weight model. The default is
  Qwen2.5-Coder-7B-Instruct served by Ollama on loopback. A hosted model is
  refused unless a flag is passed.
- **Validate** each candidate against the checks registered for the case: it
  must compile, block a reproducer and two held-out exploit variants, and pass
  the functional tests. Inputs the patch newly rejects are recorded.
- **Measure** what the patch costs on a declared workload, against the
  unpatched code, with a baseline-against-baseline noise floor.
- **Decide** which admissible patches fit a service budget declared in advance.

Each patch gets a hardening record (JSON and Markdown).

### What runs

- Two authored Java cases: `parapet/cases/C1` (CWE-502) and `parapet/cases/C2`
  (CWE-611).
- One real-library case: `parapet/cases/L1`, java-xmlbuilder pinned at a 2014
  commit with a disclosed and already fixed weakness (CVE-2014-125087,
  CWE-611). The upstream fix is one of its two reference fixes.
- Every case has a reproducer, two held-out exploit variants, functional
  tests, a workload driver, two hand-written reference fixes, and an
  incomplete control patch.
  `python -m parapet run --case C1 --budget <file>`.

### What the November 2026 evidence shows

The numbers below come from
[`evidence/mozilla-2026-11/EVIDENCE.md`](evidence/mozilla-2026-11/EVIDENCE.md),
frozen at commit `75b2b95`. They were measured on one machine and one JDK, on
single-threaded workloads written for this evaluation.

- **Checks.** In all three cases the unpatched code fails the checks, both
  reference fixes pass, and the incomplete control patch is rejected by the
  held-out variants.
- **Generator.** The local model produced admissible patches on C2 (5 of 5)
  and on L1 with a longer context window (3 of 5). It produced none on C1 (0 of
  5) or on L1 at the default settings (0 of 5; the prompt was truncated).
- **Budgets.** No generated patch fit either budget. At a 25% latency cap the
  workflow rejected every generated patch and, on L1, the upstream fix.
- **Cost.** Patches that pass the same checks differed widely in latency
  overhead: about +1.5%, +9.5% and +33% on C2, and about +11% (alternative
  fix), +40% (upstream fix) and +82% (generated) on L1.
- **Post-hoc.** A hand-written C2 patch with the same parser settings as the
  generated one, configured once instead of on every call, measured 6.6%
  faster than the unpatched code. The workflow did not produce this patch.

### Limitations

- This is a prototype. No maintainer has used it, the authored cases are
  small, and L1 is a single library at a historical commit.
- Passing the registered checks is not proof of security. Patches that pass
  can differ in coverage: L1's upstream fix still reads an external DTD named
  by the document, and the other passing patches reject such documents.
- The decision rule ranks admissible patches by cost only. It does not weigh
  rejected inputs or differences in security coverage.
- Verdicts at a 5% cap are not stable from session to session, and peak memory
  is too noisy to resolve at that level.
- Every workload is single-threaded. Concurrent load, resource contention and
  architecture-level costs are not measured.
- The generator rewrites a whole file, which fails on a large file at the
  default settings.
- One model was used. Nothing here compares models, and the extra cost of the
  generated patches is not attributed to the model: they set more parser
  features than the reference they were compared with.
- **Planned, not implemented:** choosing fixes across several weaknesses
  within one budget; repository ingestion; pull-request integration.
- **Not exercised by the workflow:** CoQuIR, LUNA, PrivAuditor, and Metior.
  PerfOrch is reused by import (its `generate_text` for every model call, its
  `run_with_timeout` for every validation run); its own measurement backend is
  not used for workload measurement.

The evidence, including every failure, is in
[`evidence/mozilla-2026-11/`](evidence/mozilla-2026-11/), with installs in
[`evidence/INSTALLS.md`](evidence/INSTALLS.md) and every change after
pre-registration in [`evidence/DEVIATIONS.md`](evidence/DEVIATIONS.md).
`VERSION` still reads 1.0, the version of record of the last release.

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
parapet/                            the hardening workflow (1.1.0-alpha): cases, budgets, stages, CLI
evidence/                           evidence package for the local slice (installs, deviations, runs)
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
It runs the unit tests of the `parapet/` workflow package (budgets, validation
semantics, decision rule, records, statistics, prompt contents) and, in the JVM
job, the C1/C2 harness against the unpatched source, the control patch, and a
reference fix. No CI job calls a model or measures performance.

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

**PARAPET 1.1.0-alpha and the Mozilla Human-Scale AI Incubator application.**
Yutong Zhao (California State University, Long Beach), Sen He (University of
Arizona), and Lu Xiao (Stevens Institute of Technology).

**PARAPET v1.0 (NSF PESOSE Track 1 baseline).** Led by California State
University, Long Beach (PI Yutong Zhao), with the Rochester Institute of
Technology (Co-PI Derui Zhu) and the University of Arizona (Co-PIs Sen He and
Bo Liu).

**Acknowledgments.** Derui Zhu's research artifacts (CoQuIR, LUNA,
PrivAuditor, and More Than Just Functional) are vendored under `projects/`,
with provenance and licenses recorded in each project folder and in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). Derui Zhu and Bo Liu
contributed to PARAPET v1.0 as co-investigators and are not participants in
the Mozilla application. The 1.1.0-alpha workflow reuses and builds on the
v1.0 code with their agreement.

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
