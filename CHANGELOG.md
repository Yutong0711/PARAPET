# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/), with one
addition: **a change to a shipped pattern set or code book is a minor
version at least, and removing a pattern is a major version**, because
both change what an existing user's queue looks like without them asking.

## [Unreleased]

### Not yet verified

The five packages in this repository have not been executed end to end.
The tests are written and the example is bundled, but neither has been run.
Do not tag a release until `make check` is green.

## [0.1.0] - unreleased

First release. Four components and the schema that lets them compose.

### Added

**`parapet-record`** — the hardening-record schema.
- Versioned record with exposure, review cost, measured cost, attribution
  and a budget verdict.
- Service budget with units on every limit; comparing a measurement
  against a limit in a different unit raises instead of returning a wrong
  answer.
- A change is admitted only when the whole confidence interval fits. A
  cost with no interval leaves the record `unscored`.
- A dimension the budget does not declare is a non-decision, not a pass.
- Provenance: SHA-256 over every input, plus the environment profile the
  measurement was taken in.

**`parapet-triage`** — routing issue reports and advisories.
- The heuristic linguistic pattern language, with a parser for the
  published notation: phrase alternation, `+` conjunction, top-level `|`
  disjunction, numbered clauses, `word_contains`, `text_contains`,
  `ner_contains`, token classes, and the ordering and repetition builtins.
- The 80 published performance patterns, bundled. Seven have malformed
  quotes or braces upstream; the parser repairs them in place and reports
  each repair rather than approximating silently.
- A 20-pattern starter set for security hardening, unvalidated and
  labelled as such.
- Transparent weighted scoring with published per-pattern precision as
  weights, so no fitting is involved and the classifier behaves
  identically everywhere. Optional trained scorer for comparison.
- Ingest from CSV, JSON, OSV advisories, GitHub issue exports and plain
  text. Nothing reaches the network.
- `classify`, `explain`, `patterns`, `doctor`.

**`parapet-scope`** — change scope and review cost.
- Java structure read from source text: packages, types, imports,
  inheritance and type references, with no build required.
- Design structure matrices and Diff-DSMs from two git revisions.
- Localized against design-level, decided by structure rather than size.
- The four design-level shapes, each with the structural evidence that
  named it, and a review order derived from it.
- The five test/production co-change patterns.
- `analyze`, `dsm`, `batch`.

**`parapet-attrib`** — where the added cost landed.
- Java call graphs from source, plus importers for java-callgraph,
  Understand, CSV and JSON.
- Profiles from CSV, JSON, JFR text output and JMH JSON.
- Attribution of a measured increase across four regions: the changed
  methods, what they call, what calls them, and everything else.
- Expensive Callee and Inefficient Caller, named with their evidence.
- A noise floor, because reporting a 0.3% regression as a finding trains a
  maintainer to ignore the tool.
- `diff`, `space`, `graph`, `hotspots`.

**`parapet`** — the chain.
- `init` writes a starter service budget; `run` produces one record from
  whichever stages have their inputs; `show` reads a record back; `doctor`
  says what is installed.
- Every stage is optional, and a stage that could not run says why.

### Known limitations

- Java only for structure and call graphs. Triage is language-agnostic.
- The Java scanner resolves types by simple name, so two same-named types
  in different packages are conflated. `--scope full` narrows this.
- The source-built call graph does not follow virtual dispatch to
  implementations.
- The security pattern set has no labelled corpus behind it.
- No release signing key exists yet.

[Unreleased]: https://github.com/Yutong0711/PARAPET/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Yutong0711/PARAPET/releases/tag/v0.1.0
