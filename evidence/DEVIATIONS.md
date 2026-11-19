# Deviations log — mozilla/local-slice

Every change to pre-registered material after the `prereg:` commit is
recorded here with its reason and time, and results are reported for both
versions. Section 1 records things a reader should know that happened BEFORE
the pre-registration commit.

## 1. Disclosures made before pre-registration

**P1. Development runs of the workload driver before pre-registration
(2026-11-18, ~16:47–16:58 PST).** While authoring the harness, I executed the
case checks and the workload driver to debug them. For C1 this printed
single-JVM timings (5 or 20 measured rounds) for the unpatched source, R1, R2
and the control patch; the R2 run was visibly faster than the baseline. For C2
the workload was timed only on the unpatched source, to choose
`ops_per_round` (600); C2's R1/R2/control workload runs were executed only to
confirm they start, with timing output suppressed. None of these runs is
evidence and none was saved. The budget caps committed in the prereg commit
(strict 5%/5%, lenient 25%/25%) were chosen before any of these runs; this
cannot be proven from the repository and is stated here so a reader can
discount accordingly.

**P2. C2 reference fixes revised before pre-registration (~16:55 PST).** After
reading the current OWASP XXE Prevention Cheat Sheet, R1 was changed from
`disallow-doctype-decl` + `setXIncludeAware(false)` to the cheat sheet's exact
DOM snippet (`disallow-doctype-decl` + `FEATURE_SECURE_PROCESSING`), and R2
from an `EntityResolver` returning empty content to one that throws
`SAXException`, as the cheat sheet states, plus `FEATURE_SECURE_PROCESSING`.
Reason: match published guidance exactly. No timing of either version was
looked at.

**P3. A harness defect found and fixed before pre-registration (~17:01 PST).**
A plumbing test showed C1's payload checks counted an unreadable fixture file
as "input rejected, canary did not fire", which would have passed the
unpatched source. Fixed: an unreadable fixture now reports `harness-error`
and fails the check, and the CLI stops a run if the unpatched source does not
fire all three canaries.

**P4. `VERSION` is not bumped to 1.1.0-alpha.** The existing structural test
suite pins `VERSION` to exactly `1.0` and requires a `\d+\.\d+` form; the task
names README.md and CHANGELOG.md as the places to state 1.1.0-alpha. The new
package reports `parapet.__version__ == "1.1.0-alpha"` and the CHANGELOG gets
an unreleased 1.1.0-alpha section; `VERSION` stays the version of record of
the last release (1.0).

## 2. Deviations after pre-registration

(none yet)
