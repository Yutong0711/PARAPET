# Security policy

## Reporting a vulnerability

Report privately, not in a public issue.

**Use [GitHub private vulnerability
reporting](https://github.com/Yutong0711/PARAPET/security/advisories/new).**
That is the primary channel. It is attached to the repository rather than
to a person, so it keeps working when maintainers or their affiliations
change, and it gives us a private place to draft the advisory and the fix
together.

If that is not available to you, email `yzhao102@stevens.edu` with
`PARAPET security` in the subject.

Include what you did, what happened, and what you expected. A reproducer
helps more than anything else.

**Response targets.** Acknowledgement within 3 working days. An initial
assessment within 10 working days. A fix or a decision not to fix within
90 days, with the reasoning published either way. We will credit you
unless you ask us not to.

We will not take legal action against good-faith research that stays
within these bounds: no access to data that is not yours, no degradation
of anyone's service, and no public disclosure before the 90 days elapse or
a fix ships, whichever comes first.

## What this project is, from a security point of view

PARAPET produces a document that a maintainer uses to decide whether to
merge a change to security-critical code. That makes the *record* the
asset, not the code that writes it. An attacker who cannot change the code
but can change what the record says has achieved the same thing: a change
moves through review on evidence that is wrong.

Everything below follows from that.

## Threat model

| # | What an attacker wants | How | What stands in the way |
| --- | --- | --- | --- |
| 1 | A record that understates the cost of a change | Choose the workload, repeat the run until it is favourable, measure on unlike hardware, hide the tail in a mean | Records carry the environment profile, the workload name and the sample count; a cost with no interval leaves the record `unscored` rather than `admitted`; the budget check requires the whole interval to fit |
| 2 | A record that overstates confidence | Feed one measurement and let it read as settled | `settled` is recorded per measurement and defaults to false for a single sample; `HardeningRecord.decide()` refuses to admit on a cost with no interval |
| 3 | A budget that quietly moves | Edit the limits file so hardening the project would otherwise accept starts failing its own check | The budget requires an `authority` field naming who may change it; a budget without one is rejected at load; changes to the file should be reviewed like changes to a signing key |
| 4 | Code execution through an input | A crafted advisory, issue body, Java source or profile | Every input is parsed, never executed. No `eval`, no `pickle`, no dynamic import of input-derived names. YAML is read with `safe_load` |
| 5 | Instructions smuggled through ingested text | An advisory or issue body that reads as a directive | The tool classifies text and never acts on it; ingested text is data on every path, and its hash goes in the record |
| 6 | A poisoned pattern set | Ship a pattern set that suppresses a class of report | Pattern sets are plain declarative YAML with no code; the set's identity and hash go in every record; `parapet-triage patterns --verbose` prints exactly what each pattern compiled to |
| 7 | A compromised release | Publish a build nobody made | Signed tags, provenance attestation on release artifacts, SBOM per release, and a two-person review requirement on the release branch |
| 8 | Standing supply-chain risk | Vulnerable or typosquatted dependency, account takeover | Near-zero dependency surface (see below); Dependabot; OpenSSF Scorecard in CI; two-factor authentication required for maintainers |

## Dependency surface

Deliberately small, because every dependency is an attack path and a
reason someone cannot install the tool.

| Package | Runtime dependencies |
| --- | --- |
| `parapet-record` | none |
| `parapet-scope` | none |
| `parapet-attrib` | none |
| `parapet-triage` | PyYAML |
| `parapet` | the four above, plus PyYAML |

Optional extras (`spacy`, `scikit-learn`) are never imported unless
explicitly requested, and the tool states in `doctor` what it is running
without.

## Open risks, with dispositions

Recorded here rather than in a private document, because a risk register
nobody can read is a risk register nobody can check.

| Risk | Disposition |
| --- | --- |
| The Java scanner resolves types by simple name, so two same-named types in different packages are conflated | **accepted**, documented in `parapet_scope.javasrc`. Mitigation: `--scope full` widens resolution. A wrong edge changes the scope verdict, not the cost measurement |
| The call graph from source misses virtual dispatch to implementations | **accepted**, documented. Mitigation: import a graph from a real analyser with `--graph` |
| The security pattern set has not been validated against a labelled corpus | **open**. Its header says so, and it is a starter set, not a detector. Building a labelled corpus is the obvious next piece of work |
| A single-sample cost is easy to produce and the record marks it `unscored`, which a hurried reader may treat as a pass | **open**. `parapet show` prints the verdict on its own line; a stronger fix is a CI mode that fails on `unscored`, which `--fail-unless-admitted` provides |
| No release signing key exists yet | **open**, blocks the first release |

## Supported versions

Pre-1.0. Only the latest release gets fixes. See `RELEASING.md` for the
support window once 1.0 ships.
