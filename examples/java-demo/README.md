# The bundled example

A complete PARAPET run on a four-class Java project, with everything it
needs in this directory. Nothing is downloaded, nothing is compiled, and
it finishes in seconds.

```bash
bash examples/java-demo/run.sh
```

Run it before pointing the tool at your own repository, so you know what
the output looks like when it works. CI runs it on every push, so if it
breaks, the quickstart is broken.

## The story it tells

`Store.read` got a bounds check. It is cheap per call and called 50,000
times per benchmark run, so the read benchmark got 12% slower.

The interesting part is where the tool says the cost is. The method that
changed is `Store.read`, but the method a maintainer is looking at is
`Loader.load`, three levels up, because that is what the benchmark
measures. A total percentage would point at `Loader.load`. The attribution
points at `Store.checkBounds`, which is where the fix belongs, and names
the shape:

```
  the added cost landed below
  pattern: Expensive Callee - Loader#load spends 96% of its time below it
```

The issue file also carries a security advisory (`DEMO-3`) and two
irrelevant reports, so you can see the triage separate them:

```bash
parapet-triage classify examples/java-demo/issues.csv --patterns security
```

## Why the record says `unscored`

Because each profile is one sample. A change is admitted only when the
whole confidence interval fits the budget, and one measurement has no
interval.

That is the point of the example ending there. A record that said
`admitted` on one sample would look exactly like a record that earned it.

## The files

```
src/acme/*.java          four classes, a call chain four deep
profile-before.csv       one run before the change
profile-after.csv        one run after
issues.csv               five reports: two relevant, one advisory, two not
parapet-budget.yaml      a real budget, with an authority and a workload
run.sh                   the whole run, five steps
```
