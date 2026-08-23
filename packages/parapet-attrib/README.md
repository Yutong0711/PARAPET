# parapet-attrib

The benchmark says the change made things 4% slower. Where did the 4% go?

```bash
pip install parapet-attrib
parapet-attrib diff \
    --source src/main/java \
    --before before.csv --after after.csv \
    --changed acme.Loader#load
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

The cost is not in the method you edited. It is one level down. That is a
different fix, and a total percentage would never have told you.

## What it costs to install

Nothing. Zero runtime dependencies. Call graphs are built from Java source
text, so there is no build step and no commercial analyser.

## Four answers, not one number

Every increase is attributed to one of four places:

| Where | What it means |
| --- | --- |
| `here` | in the methods that changed. Fix the diff |
| `below` | in what those methods call. Fix the callee |
| `above` | spread across the callers that reach them. Fix the call sites |
| `elsewhere` | outside the region the change can reach. Something else moved; repeat the measurement |

`elsewhere` is the one worth dwelling on. If most of the increase falls
outside the space of the change, the measurement is contaminated, and the
tool says so rather than attributing the number anyway.

## Two shapes it names

**Expensive Callee.** The method's own time barely moved; what it calls
got slower. The chain, not the method, is the unit of work.

**Inefficient Caller.** The method is cheap per call and did not change,
but something now calls it far more often. The fix belongs to the caller.

Both come from Zhao, Xiao, Wang, Chen, Chen and Liu, *IEEE ICSA* 2020
([10.1109/ICSA47634.2020.00027](https://doi.org/10.1109/ICSA47634.2020.00027)).

## Inputs

**Call graphs**, from any of:

```bash
--source src/main/java                       # built from Java source, no build
--graph callgraph.csv                        # two columns: caller, callee
--graph raw.txt --graph-format java-callgraph
--graph und.csv --graph-format understand
```

**Profiles**, from any of:

```bash
--profile-format csv    # method,time,own_time,count
--profile-format jfr    # jfr print --events ExecutionSample > out.txt
--profile-format jmh    # java -jar bench.jar -rf json
--profile-format json
```

JFR ships with the JDK, so it is the path that needs nothing extra:

```bash
java -XX:StartFlightRecording=filename=before.jfr -jar app.jar bench
jfr print --events ExecutionSample before.jfr > before.txt
```

## Other commands

```bash
parapet-attrib space acme.Loader#load --source src/main/java
parapet-attrib hotspots --profile after.csv --changed acme.Loader#load --source src
parapet-attrib graph --source src --output callgraph.json
```

## In CI

```bash
parapet-attrib diff ... --fail-on-regression
```

Exits 2 when total cost rose.

## What the source-built graph cannot do

A call through an interface reaches the interface's method, not the
implementation a virtual dispatch picks, so a graph from source
over-approximates upward and under-approximates across implementations.
For attributing a measured cost to a region that is enough. For anything
needing soundness it is not; import a graph from a real analyser with
`--graph`.

Unresolved call sites are counted and reported.

## Noise

`--noise-floor` (default 1%) drops changes smaller than that fraction of
the before-value. Run-to-run variation is real, and reporting a 0.3%
"regression" as a finding trains a maintainer to ignore the tool.

Apache-2.0.
