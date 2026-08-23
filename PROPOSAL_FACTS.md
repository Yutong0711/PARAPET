# Facts the PESOSE proposal needs from this repository

NSF 26-506 requires every PESOSE proposal to give "details on the current
status of the open-source product development and testing model, methods
of dissemination, user base, and contributor base." The project
description carries `\todoconfirm{...}` markers where those details go.

This file maps each marker to the artifact that answers it, so the
substitution into the `.tex` is mechanical and each claim points at
something a reviewer could check.

**Read the status column before copying anything.** Some rows are ready,
some need a command run once, and some cannot be answered by code at all.

---

## s2_product.tex

| Line | Marker | Value | Status |
| --- | --- | --- | --- |
| 36 | `download evidence` | PyPI download counts for `parapet`, `parapet-triage`, `parapet-scope`, `parapet-attrib`, plus GitHub clone and release-asset counts | **blocked**: needs a public release first. Four separately installable packages give four independent counts, which reads better than one aggregate. |
| 37 | `URL, license file` | Repository URL, and `LICENSE` (Apache-2.0, OSI-approved) with `NOTICE` for the two CC BY 4.0 bundled data sets | **ready**: `LICENSE`, `NOTICE` |
| 37 | `version, date, cadence, registry` | `0.1.0`; release date; cadence and support window in `RELEASING.md`; registry PyPI | **ready once released**: policy is written, the version and date are not real until a tag exists |
| 38 | `language ecosystems and workload classes` | Ecosystems: Java (structure and call graphs from source), and any language for triage, which is text-only. Workload classes: JMH benchmarks, JFR execution samples, and any profiler that exports method, time, own time and count to CSV. | **ready**: see `docs/java-setup.md` |
| 40 | `coverage` | Statement coverage across the four packages | **needs a run**: `make coverage` writes `docs/coverage.md` |
| 43 | `share` (reproducer cleared) | Not answerable from this repository. PARAPET's admission criteria depend on the security half: running the project's reproducer, memory checker and analyzer against each candidate. This repository has the cost half. | **out of scope here** |
| 44 | `share` (preferred candidate fits budget) | Same. The budget check is implemented (`parapet_record.schema.check_budget`), but the share of candidates that fit needs a corpus of real candidates. | **out of scope here** |

The last two rows matter. They are the V3 and V5 efficacy lines, and this
repository cannot produce them. Either the CRII tooling supplies the
regression corpus, or those numbers stay unfilled and the efficacy
thresholds in `s7_milestones.tex` are stated relative to a number the
award will measure rather than one already in hand.

---

## s5_security.tex

| Line | Marker | Value | Status |
| --- | --- | --- | --- |
| 8 | `current safeguards` | Pinned dependencies with recorded provenance; every record carries input hashes and an environment profile (`parapet_record.provenance`); OpenSSF Scorecard in CI; SBOM generated per release; signed tags; branch protection requiring review; a published disclosure policy with a private channel and response targets | **ready**: `.github/workflows/scorecard.yml`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `SECURITY.md` |

`M3`'s completion criterion is "control set v0 in force before the first
pilot" with "open risks with dispositions". `SECURITY.md` carries the
disposition table, so M3 starts from a baseline rather than from nothing.

---

## s8_team.tex

| Line | Marker | Value | Status |
| --- | --- | --- | --- |
| 23 | `maintainerships, working groups` | Maintainer of PARAPET and its four packages; other roles are the PIs' to state | **partial**: this repository substantiates the PARAPET maintainership only |
| 23 | `3--5` | Letters of collaboration from third-party users or contributors | **blocked**: cannot be produced by code. See below. |
| 25 | `count` | How many of the letters come from the pilot candidates | **blocked**: same |

### The letters are the binding constraint

NSF 26-506 requires "a minimum of three and up to five letters of
collaboration from third-party users and/or contributors of the
open-source product," and they "must be from current users or contributors
(who are not directly related to the proposing team)."

No amount of code produces those. What this repository does is remove
every obstacle between a prospective user and a first successful run:

- four packages that install with `pip` and no other tooling;
- a quickstart that ends in a real result in under an hour
  (`docs/quickstart.md`), which is also `M2`'s completion criterion;
- a worked example on a bundled Java project (`examples/`), so an
  evaluator can see the output before committing their own repository;
- explanations attached to every verdict, so a first-time user can tell
  whether the tool is right without reading the source.

Those are necessary and not sufficient. The letters need people who have
actually used it.

---

## s7_milestones.tex

| Line | Marker | Value | Status |
| --- | --- | --- | --- |
| 103 | `share` (V3 clearance rate) | Same as `s2_product.tex:43` | **out of scope here** |
| 31, 225 | consultant and I-Corps `names` | Not a code question | — |
| 227--232 | person-months, days, CPU-hours, GPU-hours | Budget, not code | — |

### M2 is the milestone this repository serves directly

> M2 (Q1): Pilot readiness: packaging and docs for partner installs
> (≤10 person-days); independent evaluator engaged. **Two installs by pilot
> candidates from docs alone (≤1 hour)**.

`docs/quickstart.md` is written against that criterion, and
`examples/java-demo` is the thing a candidate runs. Time two people
through it before the proposal goes out; if it takes longer than an hour,
the criterion is wrong or the docs are, and both are fixable now.

Note that Track 1 "awards support planning, not product development". The
work in this repository is packaging and documentation, which is what M2
describes, and the tool development it packages belongs to CRII #2544013,
as `s8_team.tex` already states. Keep that boundary visible in the budget
justification.

---

## What to do next, in order

1. **Run `make coverage`** and paste the number into `s2_product.tex:40`.
2. **Publish the repository** under the URL in `CITATION.cff` and tag
   `v0.1.0`. That makes `s2_product.tex:37` and the `parapet2026repo`
   entry in `references.bib` real; the solicitation requires a References
   Cited entry pointing at the product, because URLs are not allowed in
   the project description.
3. **Release to PyPI** and let download counts accumulate. Even a small
   number is evidence; no number is a gap a reviewer will notice.
4. **Mint a Zenodo DOI** from the first release, so the References Cited
   entry has a stable identifier rather than a bare URL.
5. **Run the quickstart against two outside projects** and record the
   wall-clock time. That is `M2`'s evidence and also the beginning of a
   user base.
6. **Ask the three pilot candidates named in `s3_discovery.tex` to try
   it.** A candidate who has run the tool can write a letter about the
   product; one who has only heard about it cannot.

---

## Numbers this repository can state today

Fill these in after `make check`, which runs the tests and writes
`docs/coverage.md`:

| Fact | Where it comes from |
| --- | --- |
| Number of installable packages | 4 (`parapet`, `parapet-triage`, `parapet-scope`, `parapet-attrib`, plus `parapet-record`) |
| Pattern set size | 80 published performance patterns, 20 starter security patterns; `parapet-triage patterns` |
| Pattern compilation fidelity | `parapet-triage patterns --verbose` reports how many needed repair and why |
| Accuracy on the published corpus | `paper/validate_on_corpus.py` writes `docs/accuracy.md` |
| Test count and coverage | `make coverage` |
| Supported ingest formats | CSV, JSON, OSV, GitHub issue export, plain text |
| Supported profile formats | CSV, JSON, JFR text, JMH JSON |
| Supported call-graph sources | Java source, java-callgraph, Understand, CSV, JSON |
