# Contributing to PARAPET

Thanks for your interest. This document covers how to get the repository
running locally, how to run the checks CI runs, and the rules that are specific
to PARAPET — chiefly that this repository redistributes other people's research
artifacts, and their provenance and licensing must survive every change.

## What lives where

PARAPET is two different kinds of content in one repository, and they are
treated differently:

| | PARAPET-owned | Vendored research artifacts |
| --- | --- | --- |
| Paths | `index.html`, `styles.css`, `script.js`, root docs, `tests/`, `scripts/`, `.github/` | everything under `projects/` |
| License | Apache-2.0 ([`LICENSE`](LICENSE)) | upstream licenses, see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) |
| Changes | normal pull requests | see "Working with vendored artifacts" below |

## Getting the repository

```bash
git clone https://github.com/Yutong0711/PARAPET.git
cd PARAPET
```

## Local setup

The supported local environment is Python 3.10 or newer on Linux or macOS. The
vendored PerfOrch modules use PEP 604 unions (`float | None`) and slotted
dataclasses, so 3.10 is a hard floor. CI runs on Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` is small on purpose: `pytest`, `numpy` (imported by
PerfOrch's runtime-processor core), and `PyYAML` (used to validate the workflow
files). Nothing in the test suite needs a GPU, a model download, an API key, or
network access at test time.

Two optional system tools widen coverage:

- a POSIX `timeout` utility — required by PerfOrch's runner; present by default
  on Linux, available on macOS via `brew install coreutils`. Without it the
  Python end-to-end tests skip.
- a JDK (`javac` and `java`) — without it the Java end-to-end tests skip.

## Running the tests

One command runs everything available on your machine:

```bash
./scripts/run_tests.sh
```

It is a transparent wrapper that prints and runs the same `pytest` invocations
CI uses. To run one suite at a time:

```bash
./scripts/run_tests.sh functional   # component functional + Python runtime smoke
./scripts/run_tests.sh jvm          # Java end-to-end smoke (needs a JDK)
./scripts/run_tests.sh sanity       # repository + website structural checks
```

Or call `pytest` directly:

```bash
python3 -m pytest tests/perforch tests/more_than_just_functional -m "not jvm"
python3 -m pytest tests/perforch -m jvm
python3 -m pytest tests/repository tests/website
```

### The three test tiers, and what they do and do not prove

These are deliberately kept apart. Do not present one as the other.

1. **Functional / unit tests** — `tests/perforch/` (excluding the runtime
   end-to-end files) and `tests/more_than_just_functional/`. These import real
   vendored modules and assert on real behaviour: function extraction across
   five languages, benchmark program assembly, prompt construction, the
   model-selection memory's aggregation and ranking, benchmark file parsing,
   and the per-language benchmark-loop transformations.

2. **End-to-end smoke tests** — `tests/perforch/test_python_runtime.py` and
   `tests/perforch/test_java_runtime.py`. These actually write a candidate to
   disk, compile it where applicable, execute it under a timeout, and check the
   reported result. They are the only tests that run generated code.

3. **Repository structural / sanity checks** — `tests/repository/` and
   `tests/website/`. These verify provenance banners, preserved upstream
   license files, version consistency, internal documentation links, that every
   vendored Python source still parses, and that the website's HTML, JavaScript
   selectors, and Pages deploy manifest agree with each other. **They are not
   functional tests of any component**, and they must never be counted as such.

### What is not tested here

Not a gap to be papered over — these components genuinely cannot run on a
hosted CI runner from this checkout:

| Component | Why not | What running it would need |
| --- | --- | --- |
| CoQuIR | retrieval evaluation only | `mteb` + a fork, `sentence-transformers`, torch, and the named retriever checkpoints; the CoQuIR datasets |
| LUNA | needs torch, sklearn, `baukit`, `flash_attn`, and LLM activations | the `eval/` (~42 MB) and `dataset/` (~7 MB) directories removed from this snapshot, plus GPU inference |
| PrivAuditor | adapter fine-tuning and membership-inference attacks | GPUs, HuggingFace model downloads, the Pile subsets |
| Metior | `MetiorArtifacts.py` runs `argparse` and loads data at import time, so it cannot be imported | the `recombinator` package, the removed `AWS/` and `Chameleon/` measurement data, and a `__main__` guard on the CLI block |
| More Than Just Functional (generation) | needs `transformers` and CUDA | GPU inference; only the AST profiler transform is tested here |
| PerfOrch Go / Rust / C++ backends | need Go with `goimports`, a Cargo toolchain, and `g++` with OpenSSL | those toolchains on the runner; only their pure transformations are unit-tested |
| PerfOrch profiling (`refine_test`) | needs the `cmdbench` package and a quiesced host | `cmdbench`, plus a dedicated machine — timing on a shared runner is not trustworthy |
| PerfOrch LLM calls | need paid model APIs | provider credentials, which CI deliberately does not have |
| Upstream vendored test suites (hmmlearn, PEFT, MIMIR) | need compiled C extensions, torch, and model downloads | the full upstream build and data for each |

If you add coverage for any of these, update this table and the corresponding
paragraph in `README.md` in the same change.

## Working with vendored artifacts

Everything under `projects/` is a snapshot of someone else's research artifact.
The rules:

- **Never overwrite or delete an upstream license file.** Not `LICENSE`, not
  `LICENSE.md`, not `LICENSE.txt`, not `DATA_LICENSE`, not a license header
  inside a source file. PARAPET's move to Apache-2.0 applies to PARAPET-owned
  content only.
- **Never relicense a vendored component**, and never infer a license from an
  upstream project's reputation or website. If a snapshot has no license file,
  it is recorded as having none in `THIRD_PARTY_NOTICES.md`.
- **A license may be added to a snapshot only on an explicit decision by the
  party that owns or controls it**, and the decision has to be recorded in
  `THIRD_PARTY_NOTICES.md` alongside its scope. That is how
  `projects/perforch/LICENSE`, `projects/luna/LICENSE`, and
  `projects/more-than-just-functional/LICENSE` came to exist: a project-team
  decision covering project-level content only. Such a decision never reaches
  third-party components nested inside the directory — hmmlearn under
  `projects/luna/src/luna/hmmlearn/` stays BSD 3-Clause.
- **Keep the provenance banner** at the top of each `projects/*/README.md`. It
  records the upstream source, commit or bundle version, and what was removed.
- **Do not edit vendored upstream README bodies.** They describe the upstream
  tree, including files this snapshot does not contain. That is expected. The
  one exception is a statement that is actively false for *this* snapshot — the
  LUNA README's License section labelled its link "FPA" while pointing at an
  Apache-2.0 file. Correct the false part only, and record the edit in
  `THIRD_PARTY_NOTICES.md`.
- **A change to vendored source must be disclosed in that snapshot's provenance
  banner**, naming the files touched, why the change was needed, and whether
  upstream carries it. Do not claim upstream has an equivalent change unless
  you have verified it. `projects/perforch/README.md` is the worked example.
- **Do not change research algorithms to make a test pass.** If a vendored
  function behaves oddly, write a test that characterises the behaviour and
  says so in the docstring — there is an example in
  `tests/perforch/test_function_extractor.py`. Changing measured or
  scientific behaviour to get a green build is not acceptable.
- If a vendored snapshot needs a genuine correction, say so in the pull request
  and explain why it does not alter the artifact's scientific behaviour.

Updating a snapshot to a newer upstream version is fine, but the provenance
banner, `THIRD_PARTY_NOTICES.md`, and any license files must be updated to match
in the same change.

## Submitting changes

1. Branch from `main`.
2. Make the change, and add or update tests for PARAPET-owned behaviour.
3. Run `./scripts/run_tests.sh` and make sure it passes.
4. Open a pull request against `main`. CI runs the same checks on every pull
   request; a red build blocks the merge, and failures must be fixed rather
   than suppressed with `continue-on-error`.
5. Describe what changed and, if you touched anything under `projects/`, what
   you did to preserve provenance.

### Things a pull request must not introduce

- API keys, tokens, passwords, or any real credential — including in tests,
  examples, or workflow files. The placeholder `"YOUR_API_KEY"` values in
  `projects/perforch/src/config/api_config.py` are inert and stay that way.
- Absolute local paths.
- Virtual environments, build caches, compiled artifacts, model weights, or
  large generated outputs.
- A test that asserts nothing meaningful, or a structural check dressed up as
  a functional one.

## Versioning

`VERSION` is the single source of truth for PARAPET's release version, and
human-facing text says "v1.0". Version strings inside `projects/` belong to
upstream artifacts — the Derui Zhu artifact bundle v1.0, PEFT `0.3.0.dev0`,
MIMIR `1.0` — and are never changed to match PARAPET's.

Add an entry to `CHANGELOG.md` for anything a user would notice.
