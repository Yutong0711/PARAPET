# Troubleshooting

Start with `parapet doctor`. It lists what is installed, what each stage
needs, and prints the `pip install` line for anything missing.

---

## Triage

**Nothing matches, and things should.**

Read one report back:

```bash
parapet-triage explain issues.csv --id THE-ID
```

If it says "no match" and lists sentences, the patterns are not finding
your project's vocabulary. Lower the threshold to see what nearly fired:

```bash
parapet-triage classify issues.csv --issue-threshold 0.3
```

Then either write patterns for the phrases your project actually uses
([pattern-sets.md](pattern-sets.md)) or accept that the shipped set is
tuned for a different corpus.

**Everything matches.**

Usually the threshold, occasionally a pattern that compiled to something
broader than intended:

```bash
parapet-triage patterns --verbose | less
```

**"expected one of ['title', 'summary', ...]"**

Your CSV has no column the loader recognises as the report text. Rename it
to `summary` or `description`, or pass `--format` and use a JSON export.

**`doctor` says six patterns run degraded.**

The simple backend guesses parts of speech from suffixes. Six of the
eighty performance patterns want a real tagger. If those six matter:

```bash
pip install 'parapet-triage[nlp]'
python -m spacy download en_core_web_sm
parapet-triage classify issues.csv --backend spacy
```

---

## Scope

**"git is not on PATH"** or **"failed: not a git repository"**

`--repo` must point at a git checkout. Run from inside it, or pass the
path.

**"changed no .java files"**

The commit touched nothing this tool models. Java only, for now.

**The scope verdict looks wrong.**

Look at the structure it saw:

```bash
parapet-scope analyze --commit HEAD --show-dsm
```

If dependencies you expect are missing, the scanner could not resolve
them. Widen the resolution:

```bash
parapet-scope analyze --commit HEAD --scope full
```

`full` reads the whole tree at both commits. Slower, and resolves
references from anywhere in the system.

**"N type reference(s) could not be resolved"**

Normal for references into dependency jars, which are not modelled. A
large number relative to the file count means `--scope full` is worth the
wait.

**A change I think is design-level came back localized.**

The rule is structural: one production file with no added or removed
dependency is localized however many lines moved. That is the published
definition, and it is deliberate. A big rewrite inside one file is a big
diff, not a design change.

---

## Attribution

**"none of the changed methods are in the call graph"**

Almost always a naming mismatch. The graph and the profile must spell a
method the same way: `package.Type#method`.

```bash
parapet-attrib graph --source src/main/java --list 20
```

Compare that against the first column of your profile CSV.

**"only 40% of the increase falls inside the space of the change"**

Something else moved during the measurement. Repeat it on a quiet machine
before acting on the number. The tool warns rather than attributing it
anyway; see [java-setup.md](java-setup.md).

**No Expensive Callee or Inefficient Caller, and I expected one.**

Both need own time, and a JFR-only profile does not have it. Use
async-profiler or a CSV export with an `own_time` column.

**The total is right but the per-method numbers look small.**

Check `--noise-floor`. It defaults to 1% and drops smaller changes.
`--noise-floor 0` shows everything.

---

## The record

**It says `unscored` and I want a verdict.**

That is the tool refusing to decide on one sample. A change is admitted
only when the whole confidence interval fits the budget, and one
measurement has no interval.

Measure several times, aggregate, and set `interval_low` and
`interval_high` on the cost. See [record-schema.md](record-schema.md).

**"budget limits latency in 'ms' but the measurement is in 's'"**

Deliberate. Convert one of them; the tool will not guess which you meant.

**"budget declares no limit for this dimension"**

Not a failure. The budget did not say anything about that dimension, so
the check declines to judge it. Add a limit if you want it decided.

**The record has a warning about `parapet-record` not being installed.**

The record was written, but with no input hashes and no environment
profile, so it cannot be verified by anyone else.

```bash
pip install parapet-record
```

---

## Something else

Open an issue with the command you ran, the output, and
`parapet doctor`. If it involves a repository you cannot share, the
Diff-DSM or graph summary is usually enough.

If it looks like a vulnerability, do not open an issue.
[SECURITY.md](../SECURITY.md).
