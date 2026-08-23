# Quickstart

The target is a real result in under an hour on your own project, on a
machine with Python and git and nothing else installed.

If any step here takes longer than its stated time, that is a bug in this
document. [Open an issue](https://github.com/Yutong0711/PARAPET/issues)
and say which step.

---

## 0. Install (2 minutes)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install parapet
parapet doctor
```

`doctor` lists the four components and what each one needs. If something
is missing it prints the exact `pip install` line.

No compiler, no commercial analyser, no model download.

---

## 1. Triage: what is this report about? (5 minutes)

Export some issues. Any CSV with an id column and a title or body column
works; so does the GitHub CLI, or a directory of OSV advisories.

```bash
gh issue list --limit 200 --json number,title,body > issues.json
parapet-triage classify issues.json
```

```
23/200 report(s) matched [performance-v1, simple backend]
  MATCH  1841   3.42  spend_time, memory, duration
  MATCH  1806   2.11  speed, iteration
    -    1799   0.00
```

Ask why:

```bash
parapet-triage explain issues.json --id 1841
```

```
1841: match (score 3.42, confidence 0.92). Patterns: spend_time, memory, duration.
  [spend_time+duration] Importing a 200 MB dump takes most of the time, about 40 minutes.
  [memory] Memory usage climbs to 6 GB before the merge finishes.
```

Two sentences, three named patterns. You can tell in five seconds whether
the tool is right.

For hardening work rather than performance, swap the set:

```bash
parapet-triage classify advisories/ --patterns security
```

**This step alone is useful.** If you stop here you have a queue you can
route. The rest is about a specific change.

---

## 2. Scope: how wide is this change? (5 minutes)

```bash
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
which five only follow it, which is a different review.

Try it across your history:

```bash
parapet-scope batch --limit 100
```

---

## 3. Attribute: the benchmark says 4% slower, where did it go? (20 minutes)

This is the step that needs measurement, so it is the slow one. You need
two profiles, before and after.

The lowest-friction path uses JFR, which ships with the JDK:

```bash
git stash                       # or check out the parent commit
java -XX:StartFlightRecording=filename=before.jfr -jar app.jar bench
jfr print --events ExecutionSample before.jfr > before.txt

git stash pop
java -XX:StartFlightRecording=filename=after.jfr -jar app.jar bench
jfr print --events ExecutionSample after.jfr > after.txt
```

JMH works too, and so does any profiler that exports method, time, own
time and count to CSV. See [java-setup.md](java-setup.md).

Then:

```bash
parapet-attrib diff \
    --source src/main/java \
    --before before.txt --after after.txt \
    --changed acme.Loader#load,acme.Cache#get
```

```
abc123: total time 12400 -> 12900 (+4.0%)
  the added cost landed below
  in changed methods +40, below +430, above +12, outside +18
  91% of the increase is inside the space of 34 method(s) (6% of the system)
    callee   Cache#fetch                                   +380
    changed  Loader#load                                    +40
  pattern: Expensive Callee - Loader#load spends 92% of its time below it, and Cache#fetch got slower
```

The 4% is not in the method you edited. It is in `Cache#fetch`, one level
down. That is a different fix.

---

## 4. Budget: does this fit what we said we would pay? (10 minutes)

```bash
parapet init
```

Edit `parapet-budget.yaml`. Two fields decide whether it is worth
anything:

```yaml
authority: >-
  Changes require review by two maintainers and a note explaining what
  workload evidence justified the new limit.
workloads:
  - "bench/read-throughput"
limits:
  latency: "5%"
binding: [latency]
```

`authority` is required; a budget nobody owns is a budget anybody can
lower. `workloads` is required in practice, because "5% slower" means
nothing until someone says at what.

Commit it. Then run everything at once:

```bash
parapet run --repo . --commit HEAD \
    --issues issues.json \
    --before before.txt --after after.txt --source src/main/java \
    --changed-methods acme.Loader#load \
    --budget parapet-budget.yaml \
    --out records/

parapet show records/HEAD.json
```

```
record a1b2c3d4  [unscored]
  exposure: 1841 (performance, no CWE)
    Importing a 200 MB dump takes most of the time
    reproducer: none recorded
    matched: spend_time, memory, duration
  review cost: design-level, Change Propagation (Type-I)
    8 production file(s), 2 test file(s)
    tests: Test Case Addition, Method Replacement
  cost: latency 12900ms (baseline 12400, no interval) on before
  the cost landed: below
    Expensive Callee: Loader#load spends 92% of its time below it
  warning: at least one cost has no interval, so the budget decision cannot be made
```

---

## Why it says `unscored`

Because you measured once. One sample has no confidence interval, and a
change is admitted only when the whole interval fits the budget.

This is the tool refusing to launder a guess into a decision. Measure
several times, and set the interval:

```bash
for i in 1 2 3 4 5; do
  java -XX:StartFlightRecording=filename=after-$i.jfr -jar app.jar bench
done
```

Then aggregate them into one profile with an interval before passing it
in; see [record-schema.md](record-schema.md) for the fields.

A record that said `admitted` on one sample would look exactly like a
record that earned it. That is the failure this refuses.

---

## Where to go next

- [Writing your own pattern set](pattern-sets.md), if the shipped ones do
  not match your project's vocabulary
- [java-setup.md](java-setup.md), if the call graph or the profile looks
  wrong
- [troubleshooting.md](troubleshooting.md)
