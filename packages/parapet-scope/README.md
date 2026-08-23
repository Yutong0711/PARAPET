# parapet-scope

How wide is this change, and where should a reviewer start?

```bash
pip install parapet-scope
cd /path/to/your/java/repo
parapet-scope analyze --commit HEAD
```

```
a1b2c3d4e5f6  AVRO-753: use a factory for encoders
a1b2c3d4e5f6: design-level, Change Propagation (Type-I).
  why: 3 new file(s) adopted by 5 existing file(s)
  8 production file(s), 12 dependency(ies) added, 1 removed.
  review in this order: EncoderFactory -> BufferedBinaryEncoder -> DirectBinaryEncoder -> RpcSendTool
  tests: Test Case Addition, Method Replacement
```

The diffstat said eight files. This says which one carries the idea and
which five only follow it.

## What it costs to install

Nothing. Zero runtime dependencies, no compiler, no commercial analyser.
Structure is read from Java source text, so it runs on a checkout you have
not built.

## What it decides

**Scope.** *Localized* is a few lines in one file. *Design-level* is a
coordinated revision of a group of files and the structure between them.
Structure decides, not size: six files that add no dependency are six
localized edits in one commit, while two files that add a new one and
re-point four dependents onto it are design-level.

**Shape.** Four recur, and each says something different to a reviewer:

| Shape | What it means | Where to start |
| --- | --- | --- |
| Change Propagation (Type-I) | a new file carries the change, existing files adopt it | the new file, then whether each adopter needed to move |
| Change Propagation (Type-II) | dependencies re-pointed among existing files | the re-pointing; this is where an API quietly widens |
| Optimization Clone | the same edit repeated across siblings | one of them, then diff the rest against it |
| Parallel Optimization | independent edits sharing a commit | separately; they only share a commit |

**Test co-change.** Which of five patterns the revision shows, which says
whether the tests check the change or merely still pass. Only
*Performance Input Revision* targets the change directly.

The taxonomy comes from Zhao, Xiao, Bondi, Chen and Liu, *IEEE TSE* 49(2),
2023 ([10.1109/TSE.2022.3167628](https://doi.org/10.1109/TSE.2022.3167628)),
derived from 570 hand-coded issues across 13 Apache projects.

## Surveying a repository

```bash
parapet-scope batch HEAD --limit 200
```

```
  a1b2c3d4e5f6  design-level  Change Propagation (Type-I)     8p  2t  AVRO-753: use a factory
  b2c3d4e5f6a1  localized                                     1p  0t  Fix off-by-one in the reader
  ...
200 revision(s): 54 design-level (27%), 31 touched tests (16%)
```

## Looking at the matrix

```bash
parapet-scope dsm --commit HEAD
parapet-scope analyze --commit HEAD --show-dsm
```

## What the scanner cannot do

It resolves types from source text, not from a compiled classpath. That
buys running without a build, and costs accuracy in known ways:

- a type used through a wildcard import is resolved by simple name, so two
  same-named types in different packages are conflated;
- a type from a dependency jar produces no edge, because only
  in-repository structure is modelled;
- generics, annotations and shadowed names can produce a reference the
  compiler would resolve elsewhere.

Unresolved references are counted and reported. `--scope full` reads the
whole tree at both commits and resolves more, slowly.

Java only for now.

## Records

```bash
parapet-scope analyze --commit HEAD --record records/
```

Fills the review-cost half of a hardening record, folding into whatever
`parapet-triage` already wrote there.

Apache-2.0.
