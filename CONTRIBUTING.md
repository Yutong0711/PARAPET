# Contributing

## Get it running

```bash
git clone https://github.com/Yutong0711/PARAPET
cd PARAPET
make install
make check
```

`make check` runs the tests, the bundled example end to end, and a build
of every package. If it is green, CI will be.

## The repository

Five packages under `packages/`, each independently installable:

```
parapet-record   the shared schema; no dependencies
parapet-triage   issue and advisory routing; PyYAML only
parapet-scope    change scope and review cost; no dependencies
parapet-attrib   cost attribution; no dependencies
parapet-cli      chains the four
```

A package's `paper/` directory holds the validation against the published
work it implements. That is not test code; it is the evidence that the
rules the tool applies came from somewhere.

## What a good change looks like

**Keep the dependency surface at zero.** Adding a runtime dependency needs
explicit consensus (see [GOVERNANCE.md](GOVERNANCE.md)). Every dependency
is an attack path and a reason someone cannot install the tool. Optional
extras are fine when the package still works without them and `doctor`
says what is missing.

**Explain the verdict, not just the number.** Every output this tool
produces feeds a human decision. If you add a check, add the sentence that
says why it fired.

**Fail loudly rather than approximately.** When the tool cannot decide, it
should say so. A record that silently omits a check looks exactly like one
that passed it, and that is the failure worth designing against.

**Write the test against the behaviour, not the implementation.** Tests
here read as claims: `test_the_whole_interval_must_fit`,
`test_comparing_across_units_raises_rather_than_guessing`. A reader should
learn the rules from the test names.

## Changing a pattern set

Pattern sets are data, and changing one silently changes what the tool
reports. Two maintainer approvals, and:

1. Say what the pattern is for and what it should not match.
2. Add a test in `tests/test_dsl.py` with a positive and a negative case.
3. Run `paper/validate_on_corpus.py` and put the before and after numbers
   in the pull request. If accuracy moved, say whether that was the point.

Removing a pattern is a breaking change to somebody's queue. Deprecate for
one minor version first.

## Changing the record schema

`parapet-record` is what makes the components compose, so a change there
touches all of them. Two approvals, and a note in `docs/decisions/`
recording the reasoning including the option not taken. A major version
bump is a decision, not a side effect.

## Commits

Sign off, which certifies the [Developer Certificate of
Origin](https://developercertificate.org/):

```bash
git commit -s -m "scope: resolve same-package references without an import"
```

Prefix the subject with the package: `triage:`, `scope:`, `attrib:`,
`record:`, `cli:`, `docs:`, `ci:`.

If a tool wrote the code, say so in the pull request description and name
the human accountable for it. It gets the same review as any other change,
plus a second reviewer when it touches a pattern set or the schema.

## Reporting a vulnerability

Not here. [SECURITY.md](SECURITY.md).

## Prose

Documentation and comments are plain, direct English. A comment says why,
not what; the code already says what. If a decision has a cost, name the
cost.
