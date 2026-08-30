# Third-party notices

PARAPET-owned repository content is licensed under the Apache License 2.0 (see
[`LICENSE`](LICENSE)). **This repository also redistributes vendored snapshots
of third-party research artifacts, and those retain their own licenses.** The
root Apache-2.0 grant does not reach into `projects/` on its own.

Everything recorded below is taken from the license, provenance, and metadata
files actually checked into this repository. No license has been inferred from
an upstream project's reputation, website, or sibling repositories.

## Project-team licensing decision (PerfOrch, LUNA, More Than Just Functional)

Three of the vendored snapshots — **PerfOrch** (`projects/perforch/`), **LUNA**
(`projects/luna/`), and **More Than Just Functional**
(`projects/more-than-just-functional/`) — are owned or controlled by the project
team, which holds the authority to license them. The project team has decided to
release the **project-level content** of those three directories under the
**Apache License 2.0**. Each directory now carries the canonical Apache-2.0 text
in its own `LICENSE` file:

- `projects/perforch/LICENSE`
- `projects/luna/LICENSE`
- `projects/more-than-just-functional/LICENSE`

**Scope limit.** That decision covers project-level content only. It does **not**
relicense any third-party component nested inside those directories. In
particular, hmmlearn under `projects/luna/src/luna/hmmlearn/` remains under its
own BSD 3-Clause license (`projects/luna/src/luna/hmmlearn/LICENSE.txt`),
unchanged and unaffected. Every other nested license file, attribution,
copyright notice, and provenance statement in this repository is likewise
unchanged.

The Apache-2.0 files added under `projects/` are the canonical license text as
published at <https://www.apache.org/licenses/LICENSE-2.0.txt>, including its
unfilled `Copyright [yyyy] [name of copyright owner]` appendix line. No
copyright holder or year has been invented for these snapshots.

Before redistributing, publishing, or building on any component, read the
license file inside that component's directory.

## Summary

| Component | Directory | License as checked in | Source of that license | License file in this repository |
| --- | --- | --- | --- | --- |
| PerfOrch | `projects/perforch/` | Apache License 2.0 | Project-team decision | `projects/perforch/LICENSE` |
| CoQuIR | `projects/coquir/` | Apache License 2.0 | Supplied upstream | `projects/coquir/LICENSE` |
| Metior | `projects/metior/` | BSD License 2.0 (statement only, not full text) | Supplied upstream | `projects/metior/LICENSE.md` |
| LUNA | `projects/luna/` | Apache License 2.0 (project-level content only) | Project-team decision | `projects/luna/LICENSE` |
| PrivAuditor | `projects/privauditor/` | Apache License 2.0 | Supplied upstream | `projects/privauditor/LICENSE` |
| PrivAuditor datasets | `projects/privauditor/` | Open Data Commons Attribution License (ODC-By) | Supplied upstream | `projects/privauditor/DATA_LICENSE` |
| More Than Just Functional | `projects/more-than-just-functional/` | Apache License 2.0 | Project-team decision | `projects/more-than-just-functional/LICENSE` |

Third-party components nested *inside* those snapshots. **None of these is
covered by the project-team Apache-2.0 decision above; each keeps the license it
arrived with:**

| Nested component | Directory | Upstream license as checked in | License file in this repository |
| --- | --- | --- | --- |
| PEFT fork (LLM-Adapters) | `projects/privauditor/src/peft/` | Apache License 2.0 | `projects/privauditor/src/peft/LICENSE` |
| MIMIR | `projects/privauditor/src/mia-attack/mimir/` | MIT License | `projects/privauditor/src/mia-attack/mimir/LICENSE` |
| hmmlearn | `projects/luna/src/luna/hmmlearn/` | BSD 3-Clause | `projects/luna/src/luna/hmmlearn/LICENSE.txt` |

## Component detail

### PerfOrch — `projects/perforch/`

- Origin: <https://github.com/qzydustin/perforch> at commit `e873cd9`, fetched
  2026-08-28 (recorded in `projects/perforch/README.md`).
- License: **Apache License 2.0** — `projects/perforch/LICENSE`. This snapshot
  arrived without a license file at its root; the file present here was added by
  the project team, which owns or controls this artifact and decided to release
  its project-level content under Apache-2.0. It is the canonical Apache-2.0
  text, with no copyright holder or year filled in.
- No third-party component is nested inside this snapshot.
- **This snapshot is not byte-identical to upstream.** It carries one
  PARAPET-maintained portability fix, in
  `projects/perforch/src/runtime_processors/core.py` and
  `projects/perforch/src/runtime_processors/python_processor.py`: the runtime
  launches candidates through an argv list rather than a shell command string,
  so an interpreter or checkout path containing a space is no longer split into
  two arguments. The fix is not present at the pinned commit `e873cd9`; whether
  upstream has since made an equivalent change has not been verified. No
  measurement, benchmark, or code-generation behavior was altered, and the
  change is recorded in the provenance banner of
  `projects/perforch/README.md`.
- The upstream `data/` directory of benchmark result JSONs (~16 MB) was not
  vendored.

### CoQuIR — `projects/coquir/`

- Origin: *PESOSE — Derui Zhu Prior Research Code Artifacts* bundle (v1.0,
  2026-08-23), `research_artifacts/coquir`. Paper: CoQuIR, ACL 2026.
- License: Apache License 2.0 — `projects/coquir/LICENSE`.
- Scope note: `projects/coquir/PESOSE_ROLE.md`.

### Metior — `projects/metior/`

- Origin: ASE 2021 research artifact for "Performance Testing for Cloud
  Computing with Dependent Data Bootstrapping" (He et al.).
- License: `projects/metior/LICENSE.md` states *"The source code is provided
  under BSD License 2.0."* The artifact supplies that statement only; it does
  not include the full BSD-2-Clause text or a named copyright holder.
- The paper PDF, `INSTALL.pdf`, `Prep/` duplicates, and the `AWS/` and
  `Chameleon/` measurement-data directories were not vendored.

### LUNA — `projects/luna/`

- Origin: *PESOSE — Derui Zhu Prior Research Code Artifacts* bundle (v1.0,
  2026-08-23), `research_artifacts/luna`. Paper: LUNA, IEEE TSE 2024.
- License (project-level content): **Apache License 2.0** —
  `projects/luna/LICENSE`. This snapshot arrived without a license file at its
  root; the file present here was added by the project team, which owns or
  controls this artifact and decided to release its project-level content under
  Apache-2.0. It is the canonical Apache-2.0 text, with no copyright holder or
  year filled in.
- The vendored `projects/luna/README.md` has a "License" section linking to
  `LICENSE`. Its label previously read "FPA", which named neither the file it
  pointed at nor any license the project team granted. PARAPET corrected that
  one label to "Apache License 2.0" and added a sentence recording that the
  bundled `src/luna/hmmlearn` component is excluded and stays BSD 3-Clause. No
  other part of the upstream README body was changed.
- Nested third-party component: **hmmlearn**
  (`projects/luna/src/luna/hmmlearn/`), BSD 3-Clause, Copyright (c) 2014
  hmmlearn authors and contributors — `projects/luna/src/luna/hmmlearn/LICENSE.txt`
  and `AUTHORS.rst`. **hmmlearn is not covered by the project-team Apache-2.0
  decision.** Its BSD 3-Clause license file is unchanged and was not replaced by
  `projects/luna/LICENSE`.
- The upstream `eval/` derived results (~42 MB) and `dataset/` (~7 MB) were not
  vendored.

### PrivAuditor — `projects/privauditor/`

- Origin: *PESOSE — Derui Zhu Prior Research Code Artifacts* bundle (v1.0,
  2026-08-23), `research_artifacts/privauditor`. Paper: PrivAuditor, NeurIPS
  2024 Datasets & Benchmarks.
- Code license: Apache License 2.0 — `projects/privauditor/LICENSE`.
- Data license: Open Data Commons Attribution License (ODC-By) —
  `projects/privauditor/DATA_LICENSE`.
- `projects/privauditor/README.md` carries a "Copyright 2023 The HuggingFace
  Team. All rights reserved." Apache-2.0 header comment, retained as supplied.
- Nested third-party components:
  - **PEFT fork** (`projects/privauditor/src/peft/`) — Apache License 2.0,
    `projects/privauditor/src/peft/LICENSE`. `setup.py` records
    `name="peft"`, `version="0.3.0.dev0"`, author "The AGI-Edgerunners team",
    url <https://github.com/AGI-Edgerunners/LLM-Adapters>.
    Within that fork, `src/peft/tuners/lora.py` and
    `src/peft/tuners/bottleneck.py` carry retained MIT headers for code derived
    from <https://github.com/microsoft/LoRA> ("Copyright (c) Microsoft
    Corporation. All rights reserved. Licensed under the MIT License (MIT).").
  - **MIMIR** (`projects/privauditor/src/mia-attack/mimir/`) — MIT License,
    Copyright (c) 2023 Anshuman Suri. `setup.py` records `version="1.0"`,
    url <https://github.com/iamgroot42/mimir>.

### More Than Just Functional — `projects/more-than-just-functional/`

- Origin: *PESOSE — Derui Zhu Prior Research Code Artifacts* bundle (v1.0,
  2026-08-23), `research_artifacts/more-than-just-functional`. Paper: "More Than
  Just Functional: LLM-as-a-Critique for Efficient Code Generation," NeurIPS
  2025.
- License: **Apache License 2.0** —
  `projects/more-than-just-functional/LICENSE`. This snapshot arrived without a
  license file at its root; the file present here was added by the project team,
  which owns or controls this artifact and decided to release its project-level
  content under Apache-2.0. It is the canonical Apache-2.0 text, with no
  copyright holder or year filled in.
- No third-party component is nested inside this snapshot.

## Known gaps

These are recorded rather than resolved, because resolving them requires a
decision from the upstream authors or the project team:

1. Metior supplies a one-line license statement ("BSD License 2.0") rather than
   full license text or a named copyright holder.
2. The Apache-2.0 files added for PerfOrch, LUNA, and More Than Just Functional
   carry the canonical text's unfilled `Copyright [yyyy] [name of copyright
   owner]` appendix line. No repository file states an authoritative copyright
   holder or year for these three artifacts, so none was invented.

Resolved since the previous revision:

- PerfOrch, LUNA, and More Than Just Functional previously had no license file
  in this repository. The project team has now released their project-level
  content under Apache-2.0 (see "Project-team licensing decision" above).
- The "License" section of the vendored `projects/luna/README.md` previously
  labelled its link "FPA", which matched neither the file it pointed at nor the
  license the project team granted. It now reads "Apache License 2.0" and names
  the hmmlearn exclusion.

The version numbers referenced above (`v1.0` for the Derui Zhu artifact bundle,
`0.3.0.dev0` for the vendored PEFT fork, `1.0` for MIMIR) are **upstream**
version identifiers and are unrelated to PARAPET's own release version.
