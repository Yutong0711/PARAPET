# Java setup

Two inputs need explaining: the call graph and the profile. Neither needs
a commercial tool, and the default path for both needs nothing beyond the
JDK you already have.

## Call graphs

### From source, no build

```bash
parapet-attrib graph --source src/main/java --output callgraph.json
```

Reads the source text. No compile step, no classpath, runs on a checkout
in seconds.

What it gets wrong, and it is worth knowing before you rely on it:

- a call through an interface reaches the interface's method, not the
  implementation virtual dispatch would pick;
- a method name declared by two types resolves only when exactly one is a
  candidate, otherwise the call site is recorded as unresolved;
- calls into dependency jars produce no edge, because only your code is
  modelled.

`parapet-attrib graph --source ... ` prints how many call sites went
unresolved. If that number is large relative to the graph, use a real
analyser.

### From java-callgraph, free and static

```bash
wget https://github.com/gousiosg/java-callgraph/releases/.../javacg-static.jar
java -jar javacg-static.jar target/app.jar > raw.txt
parapet-attrib graph --graph raw.txt --graph-format java-callgraph \
    --output callgraph.json
```

Needs a built jar, resolves bytecode rather than text, and is the right
choice when the source-built graph looks wrong.

### From Understand, commercial

Export a dependency report as CSV, then:

```bash
parapet-attrib graph --graph und.csv --graph-format understand \
    --output callgraph.json
```

### From anything else

Two columns:

```csv
caller,callee
acme.Loader#load,acme.Cache#get
acme.Cache#get,acme.Store#read
```

## Method names

One spelling everywhere: `package.Type#method`.

The importers normalise `a.Foo:bar` and `a.Foo.bar` into `a.Foo#bar`, so a
profile from one tool and a graph from another can be joined without
string surgery on your side. If your two inputs disagree, that is what to
check first: `parapet-attrib diff` warns when a changed method is not in
the graph, and a name mismatch is almost always the cause.

## Profiles

### JFR, ships with the JDK

The lowest-friction path, because there is nothing to install.

```bash
java -XX:StartFlightRecording=filename=before.jfr,settings=profile \
     -jar app.jar bench
jfr print --events ExecutionSample before.jfr > before.txt

# ... apply the change ...

java -XX:StartFlightRecording=filename=after.jfr,settings=profile \
     -jar app.jar bench
jfr print --events ExecutionSample after.jfr > after.txt

parapet-attrib diff --before before.txt --after after.txt \
    --source src/main/java --changed acme.Loader#load
```

JFR sampling gives a relative time and a sample count, not an own time.
The missing field stays empty rather than being invented, which means the
Expensive Callee and Inefficient Caller patterns cannot fire on a
JFR-only profile. Use async-profiler or a CSV export if you need them.

### JMH

```bash
java -jar target/benchmarks.jar -rf json -rff before.json
# ... apply the change ...
java -jar target/benchmarks.jar -rf json -rff after.json

parapet-attrib diff --before before.json --after after.json \
    --profile-format jmh --source src/main/java --changed acme.Loader#load
```

JMH measures benchmarks, not every method, so the profile is sparse. That
is the right input when the question is what a change did to the
benchmarks a project already runs, which is usually the question a service
budget is written against.

### CSV, from anything

```csv
method,time,own_time,count
acme.Loader#load,1000.0,40.0,50000
acme.Cache#get,900.0,60.0,50000
```

Column names are matched loosely: `total time`, `cumtime`, `self time`,
`tottime`, `ncalls` and similar all work.

## Measuring so the number means something

The tool will happily attribute a single-sample difference and the record
will come back `unscored`, which is correct and also not useful. To get a
decidable record:

**Run several times.** Five is a common minimum. Take the interval from
the spread, not from one run.

**Quiesce the machine.** No other builds, no browser, no laptop on
battery. Fix the CPU governor if you can.

**Warm up.** The JVM's first iterations measure the JIT, not your code.
JMH handles this; a bare `java -jar` does not.

**Use the workloads the budget names.** A budget says "5% on
bench/read-throughput". Measuring something else and comparing against
that limit is not a check, it is a coincidence.

**Record the environment.** `parapet-record` does this for you; a cost
number without the machine it came from cannot be compared to the next
one.

## When the attribution says `elsewhere`

Most of the increase fell outside the region your change can reach. That
usually means something else moved during the measurement: a background
process, a different JIT decision, a different input. Repeat it before
acting on the number. The tool warns rather than attributing it anyway.
