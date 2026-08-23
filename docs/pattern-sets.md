# Writing a pattern set

A pattern set is a YAML file. Each entry has a name, a category and a
definition, and the definition is written in a small language designed so
a maintainer can read a rule and predict what it matches.

```yaml
set_id: acme-v1
description: Patterns for how our project talks about slowness.
patterns:
  - id: ACME001
    name: unbounded_read
    category: STR
    definition: '{"read" | "reads"} + {"without" | "no"} + {"limit" | "bound"}'
```

```bash
parapet-triage classify issues.csv --patterns acme-v1.yaml
```

## The language

| Form | Meaning |
| --- | --- |
| `{"a" \| "b"}` | any of these phrases appears |
| `"a"` | this phrase appears |
| `X + Y` | both X and Y appear, in any order |
| `X \| Y` | X or Y, when the `\|` sits outside any brace |
| `1. X; 2. Y` | X or Y; `;` and `N.` both start a new clause |
| `word_contains{"pre"}` | some token contains this substring |
| `text_contains{"a b"}` | the substring appears anywhere |
| `ner_contains_"PERCENT"` | a named entity of this type is present |
| `NUMBER` | a numeral is present |
| `DURATION` | a duration is present |
| `VB` / `NN` | a verb / a noun is present |
| `"x" is noun` | this word appears tagged as a noun |
| `"a" is before "b"` | both appear, `a` first |
| `two nouns are the same` | a noun repeated around a joining word, as in "byte by byte" |
| `per_NN_per_NN` | `per <noun> ... per <noun>` |

Phrases match on word boundaries, so `{"reduce"}` does not fire on
"irreducible". Internal whitespace is relaxed, so `{"speed up"}` finds
"speed\n up".

Everything is case-insensitive.

## Categories

`LEX` lexical, `STR` structural, `SEM` semantic, `PRF` profiling. They are
documentation, not behaviour: nothing in the matcher reads the category.
They exist so a reader can see the shape of a set at a glance.

## Weights

Add a `precision` field and the scorer uses it as the pattern's weight. A
pattern that is right nine times in ten should count for more than one
that is right seven times in ten.

```yaml
  - id: ACME001
    name: unbounded_read
    category: STR
    precision: 0.92
    definition: '...'
```

Without a `precision`, a pattern counts 0.90, which is exactly the
sentence threshold. That is deliberate: a set you write yourself has no
precisions in it, and one hit has to be able to fire on its own.

## Check what it compiled to

Before trusting a set, read it back:

```bash
parapet-triage patterns --patterns acme-v1.yaml --verbose
```

```
  ACME001 unbounded_read (STR)
    definition: {"read" | "reads"} + {"without" | "no"} + {"limit" | "bound"}
    compiled:   ({"read" | "reads"} + {"no" | "without"} + {"bound" | "limit"})
```

A pattern that compiled to something you did not intend is the commonest
mistake, and it is invisible until you look.

## Thresholds

A sentence matches when the weighted sum of its patterns reaches
`--sentence-threshold` (0.90 by default: one confident pattern). An issue
matches when its strongest sentence plus a diminishing bonus for
corroboration reaches `--issue-threshold` (0.90, so one matching sentence
carries the issue).

The diminishing bonus is deliberate. One decisive sentence should be
enough, and ten weak ones should not add up to the same thing.

Sweep before you settle on a value:

```bash
python paper/validate_on_corpus.py --workbook "Manual Tagging.xlsx" --sweep
```

## Writing a set that works

**Start from real reports.** Read fifty issues from your own tracker and
write down the phrases people actually use. A pattern derived from how you
think people talk will not fire.

**One idea per pattern.** A pattern that matches three unrelated things
cannot be evaluated, tuned or removed.

**Prefer conjunction to a long alternation.** `{"cache"} + {"miss"}` is
almost always better than `{"cache miss" | "cache misses" | "cache-miss"}`,
because it survives phrasings you did not think of.

**Write the negative case first.** Decide what the pattern must *not*
match, then write the test, then write the pattern.

**Measure.** A set without a labelled sample of your own issues is a
guess. Two hundred hand-labelled reports is enough to tell a useful
pattern from a plausible one.

## The shipped sets

`performance` is 80 patterns, derived over 13 Apache projects and
validated on a corpus of about 13,000 hand-tagged sentences. It is the one
to imitate.

`security` is 20 patterns and has no corpus behind it. Its header says so.
It routes; it does not detect.
