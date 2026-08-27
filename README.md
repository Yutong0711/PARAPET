# PARAPET

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
it, what it cost, and how to reproduce both. This repository is the PESOSE
Track 1 planning platform: it scopes whether and how PARAPET should become a
governed open-source ecosystem.

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
evidence for the drafting workflow. **PARAPET itself — the exposure-to-decision
framework, the threat model, the security policy, repository ingestion and
pull-request integration — is built under the award and released separately.**

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
```

Each project folder is a **vendored snapshot**: source under `src/`, the
project's own `README.md` (with a provenance banner) and any upstream `LICENSE`
at the folder root. Derived results, evaluation dumps, datasets, virtualenvs,
and duplicate document formats were removed to keep this repository lightweight —
each folder README points back to the full upstream material.

| Project | Origin | Paper | Role |
| --- | --- | --- | --- |
| PerfOrch | [qzydustin/perforch](https://github.com/qzydustin/perforch) `e873cd9` | — | Seed pipeline |
| CoQuIR | Derui Zhu artifact bundle v1.0 | ACL 2026 | Core |
| Metior | ASE 2021 research artifact (He et al.) | ASE 2021 | Supporting |
| LUNA | Derui Zhu artifact bundle v1.0 | IEEE TSE 2024 | Supporting |
| PrivAuditor | Derui Zhu artifact bundle v1.0 | NeurIPS 2024 D&B | Supporting |
| More Than Just Functional | Derui Zhu artifact bundle v1.0 | NeurIPS 2025 | Background |

## What Track 1 scopes

- **Ecosystem discovery (PA1):** quota-sampled maintainer interviews, repository
  mining of how often hardening is reverted or reopened citing runtime cost, and
  three pilot integrations scored by an independent evaluator.
- **Organization and governance (PA2):** who holds authority over a declared
  service budget, who owns the non-code assets (benchmark workloads, pattern
  catalog, tuned weights), and what pays for the ecosystem. Apache-2.0 core
  weighed against MPL-2.0, paired with a contributor agreement or DCO.
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

The PARAPET platform (website, documentation, and the integration glue in this
repository) is released under the [MIT License](LICENSE). Each vendored project
under `projects/` retains its own upstream license; see the `LICENSE` file inside
that folder where present.
