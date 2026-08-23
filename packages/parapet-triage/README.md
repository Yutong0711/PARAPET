# parapet-triage

Route issue reports and advisories by what they describe, with named
patterns instead of an opaque model.

```bash
pip install parapet-triage
parapet-triage classify issues.csv
```

```
23/200 report(s) matched [performance-v1, simple backend]
  MATCH  1841   3.42  spend_time, memory, duration
  MATCH  1806   2.11  speed, iteration
    -    1799   0.00
```

Every verdict names the patterns that produced it, so you can tell in five
seconds whether it is right:

```bash
parapet-triage explain issues.csv --id 1841
```

```
1841: match (score 3.42, confidence 0.92). Patterns: spend_time, memory, duration.
  [spend_time+duration] Importing a 200 MB dump takes most of the time, about 40 minutes.
  [memory] Memory usage climbs to 6 GB before the merge finishes.
```

## What it costs to install

PyYAML. Nothing else. No model download, no training corpus, no compiler.
The classifier is a weighted sum over named patterns with published
weights, so it behaves identically on every machine and needs no fitting.

Optional extras add spaCy (part-of-speech tags and named entities, which
six of the eighty performance patterns want) and scikit-learn (a trained
scorer, if you want to check the transparent one against a fitted one on
your own data). `parapet-triage doctor` says what is installed and which
patterns are running degraded without it.

## Pattern sets

Two ship with the package.

**`performance`** is the published set of 80 patterns from Zhao, Xiao and
Wong, *IEEE TSE* 50(7), 2024
([10.1109/TSE.2024.3390623](https://doi.org/10.1109/TSE.2024.3390623)),
derived over 13 Apache projects and validated on a labelled corpus of
13,000 sentences. It is bundled under CC BY 4.0; see the repository
`NOTICE`.

**`security`** is a 20-pattern starter set for hardening work, in the same
format. It has **not** been validated against a labelled corpus and says
so in its own header. It is a router, not a detector.

Write your own:

```yaml
set_id: my-set-v1
patterns:
  - id: MY001
    name: unbounded_read
    category: STR
    definition: '{"read" | "reads"} + {"without" | "no"} + {"limit" | "bound"}'
```

```bash
parapet-triage classify issues.csv --patterns my-set.yaml
```

The pattern language is small: phrase alternation in braces, `+` for
conjunction, `|` outside braces for disjunction, `word_contains{...}` and
`text_contains{...}`, and a few token-class terms. See
[docs/pattern-sets.md](../../docs/pattern-sets.md).

## Reading a set before you trust it

```bash
parapet-triage patterns --verbose
```

Prints what every pattern compiled to, and flags the ones that needed
repair because the published definition had an unbalanced quote or brace.
Seven of the eighty do. The repairs are reported, not hidden.

## Ingest

CSV, JSON, OSV advisories (a file or a directory), a GitHub issue export,
or plain text. Column names are matched loosely, so an export from Jira,
GitHub or a spreadsheet usually works unchanged. Nothing reaches the
network: an advisory feed is a file you downloaded, which keeps a run
reproducible and lets an air-gapped project use the tool at all.

```bash
gh issue list --limit 500 --json number,title,body > issues.json
parapet-triage classify issues.json

parapet-triage classify advisories/ --patterns security
```

## In CI

```bash
parapet-triage classify new-issues.csv --patterns security --fail-on-match
```

Exits 2 when anything matches, which makes a useful gate on an inbox.

## Records

```bash
parapet-triage classify issues.csv --record records/
```

Writes one hardening record per matching report, filling the exposure
half. Install `parapet-record` alongside and the record also carries input
hashes and an environment profile; without it the record still exists and
says that it is unverifiable.

## Accuracy

`paper/validate_on_corpus.py` scores the shipped set against the published
labelled corpus and writes `docs/accuracy.md`. Run it after changing a
pattern, a threshold or the backend; the numbers the README quotes come
from there, and if they move the README moves with them.

Apache-2.0.
