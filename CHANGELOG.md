# Changelog

All notable changes to this repository are recorded here.

Version numbers refer to **PARAPET's own** release version, tracked in
[`VERSION`](VERSION). Version strings inside `projects/` belong to upstream
research artifacts and are unrelated.

## v1.1.0-alpha (unreleased; branch `mozilla/local-slice`)

### Added

- `parapet/`, the hardening workflow as a Python package (Apache-2.0):
  `budget.py` (load and validate `parapet.budget.yaml`; strict and lenient
  profiles in `parapet/budgets/`), `generate.py` (k candidates from a local
  open-weight model through PerfOrch's `llm_generator.generate_text`; hosted
  generators refused unless `--allow-hosted-control`), `validate.py`
  (compile, reproducer, two held-out variants, functional tests, probes for
  inputs the patch now rejects), `measure.py` (forked JVMs per arm,
  interleaved, warm-up discarded, raw samples, ratio of medians with a 95%
  bootstrap interval, A/A noise floor), `decide.py` (a patch fits only if the
  upper interval bound is at or below each cap), `record.py` (hardening
  records, JSON and Markdown), and the CLI `python -m parapet run --case C1
  --budget <file>`.
- Two authored Java cases: `parapet/cases/C1` (CWE-502) and
  `parapet/cases/C2` (CWE-611), each with two hand-written reference fixes
  citing published guidance and one incomplete control patch.
- `tests/parapet/`: unit tests for budget, validate, decide, record, stats,
  and the prompt; JVM tests that run the real case harness. Wired into
  `scripts/run_tests.sh` and both relevant CI jobs.
- `evidence/`: installs, deviations, and the November 2026 evidence package.

### Scope

- The four-stage workflow runs per weakness on two authored cases. Choosing
  fixes across several weaknesses within one budget is planned, not built.
- CoQuIR, LUNA, PrivAuditor, and Metior are not exercised.
- `VERSION` is unchanged (1.0): the structural tests pin it, and this
  version is not released.

## v1.0

First public release of the PARAPET repository.

This is a repository release: it publishes the vendored research artifacts, the
project website, and the automated validation around them. It does not ship an
implementation of the PARAPET framework itself — see "What is in this release"
in [`README.md`](README.md).

### Added

- `VERSION` as the single source of truth for PARAPET's release version.
- An automated test suite under `tests/`, split into three tiers that are
  reported separately: component functional tests, end-to-end runtime smoke
  tests, and repository structural checks.
- `scripts/run_tests.sh`, one documented command that runs the supported
  checks and mirrors what CI runs.
- `.github/workflows/ci.yml` — continuous integration on pull requests
  targeting `main`, pushes to `main`, and manual dispatch.
- `.github/workflows/release-check.yml` — validation that runs on a `v*` tag
  and confirms the tag matches `VERSION`. It publishes nothing.
- `THIRD_PARTY_NOTICES.md`, recording every vendored component, the license
  actually checked in for it, and where that license came from.
- `projects/perforch/LICENSE`, `projects/luna/LICENSE`, and
  `projects/more-than-just-functional/LICENSE` — the canonical Apache License
  2.0 text. The project team owns or controls these three artifacts and decided
  to release their project-level content under Apache-2.0. The decision covers
  project-level content only and relicenses no nested third-party component.
- `CONTRIBUTING.md`, including the rules for preserving vendored provenance and
  the list of components that cannot be tested in CI, with what each would need.
- A root `.gitignore`, `pytest.ini`, and `requirements-dev.txt`.

### Changed

- The PARAPET-owned repository content is now licensed under the Apache License
  2.0. `LICENSE` holds the canonical Apache-2.0 text, and `README.md` — which
  previously described the project as MIT-licensed — now states the Apache-2.0
  license and the boundary against the vendored artifacts.
- `README.md` gained CI, license, and version badges, a statement of what the
  release does and does not contain, and instructions for running the tests.
- The website footer now names the licence and version of the published content.
- `.github/workflows/pages.yml` now validates the site before deploying it;
  the deployment itself is unchanged and still runs only from `main`.
- The `PESOSE_ROLE.md` notes under `projects/` no longer point at
  `docs/ARTIFACT_SCOPE.md`, `docs/LICENSE_AND_PROVENANCE.md`, or
  `scripts/run_coquir_security_eval.sh`, none of which exist in this
  repository. They now point at `THIRD_PARTY_NOTICES.md`.

### Fixed

- PerfOrch's runtime launched candidates through a shell command string built
  by interpolating `sys.executable` (`f"{PYTHON_BIN} main.py"`), which
  `core.run_with_timeout` and `core._run_cmdbench` then re-split with
  `shlex.split`. An interpreter or checkout path containing a space was
  therefore torn into two arguments, and the Python backend failed every
  candidate with `timeout: failed to execute process: No such file or
  directory`. `projects/perforch/src/runtime_processors/core.py` and
  `projects/perforch/src/runtime_processors/python_processor.py` now pass an
  argv list straight to `subprocess` — no shell parsing, no `shell=True`.
  Timeout, stdout/stderr capture, exit-code handling, process-group cleanup,
  and correctness-test semantics are unchanged; literal command strings are
  still accepted for the Java, C++, Go, and Rust backends. Covered by
  `tests/perforch/test_runtime_path_safety.py`.

### Preserved

- Every upstream license file under `projects/` is unchanged: CoQuIR
  (Apache-2.0), Metior (BSD 2.0 statement), PrivAuditor (Apache-2.0 and
  ODC-By), the vendored PEFT fork (Apache-2.0), MIMIR (MIT), and hmmlearn
  (BSD-3-Clause). In particular, the Apache-2.0 license added for LUNA sits at
  `projects/luna/LICENSE` and did not replace or alter
  `projects/luna/src/luna/hmmlearn/LICENSE.txt`.
- Every vendored `README.md` body, provenance banner, and copyright statement
  is unchanged, with two recorded exceptions, both disclosed in place:
  `projects/perforch/README.md` gained a "PARAPET-maintained change" note (see
  Fixed below), and the License section of `projects/luna/README.md` had its
  link label corrected from "FPA" — which named neither the file it pointed at
  nor any license the project team granted — to "Apache License 2.0", plus a
  sentence excluding the nested hmmlearn component.
