# Governance

Draft. This document is early and is expected to change; it is written
down now so that the change is visible rather than remembered
differently by different people.

## What is being governed

Three things, and they need different rules.

**The code.** Ordinary open-source practice applies: pull requests,
review, a merge.

**The pattern sets and code books.** These are data, not code, and a
change to them silently changes what the tool reports. A pattern removed
from the security set is a class of report that stops being routed. They
are versioned with their own identifiers and every record names the set
and its hash, so a change is detectable after the fact.

**A project's service budget.** Not held here at all: it lives in the
project being hardened. But PARAPET defines the format and checks against
it, so the format has to make the authority explicit, and it does: a
budget file without an `authority` field is rejected at load. See
[SECURITY.md](SECURITY.md), risk 3.

## Roles

**Users** run the tool. They open issues, and they are the reason the
quickstart is measured in minutes.

**Contributors** send pull requests. No agreement to sign; the Developer
Certificate of Origin applies through a `Signed-off-by` line.

**Maintainers** merge. A maintainer may merge a change to code after one
other maintainer approves. Two approvals are required for a change to a
shipped pattern set, to the record schema, or to anything under
`.github/workflows/`.

**The schema owner** is the maintainer accountable for
`parapet-record`. Because every component writes into one schema, an
uncoordinated change there breaks all of them; a major version bump is a
decision, not a side effect.

Current maintainers are listed in `MAINTAINERS.md`. That list is the
authoritative one.

## Decisions

Lazy consensus for ordinary changes: propose in an issue or a pull
request, and if nobody objects within five working days, proceed.

Explicit consensus for changes that alter what an existing user gets
without them asking:

- removing or redefining a shipped pattern;
- changing a default threshold;
- a breaking change to the record schema;
- adding a runtime dependency;
- changing the release or signing process.

Explicit consensus means every maintainer has responded and none objects.
An unresolved objection escalates to a decision recorded in
`docs/decisions/`, with the reasoning, including the reasoning for the
option not taken.

## Changes to agent-authored contributions

PARAPET is built to be operated by an automated system, so it will receive
contributions from one. A pull request whose code was written by a tool
must say so in the description, name the human accountable for it, and
carry the same `Signed-off-by`. It gets the same review as any other
change, plus a second reviewer when it touches a pattern set or the
schema.

This paragraph is deliberately narrow and will need to widen. It is here
because a project that accepts machine-authored changes to
security-relevant code and has no policy is making a decision by not
making one.

## Adding and removing maintainers

A maintainer is added by explicit consensus of the current maintainers,
after sustained contribution. Sustained means over months, not commits.

A maintainer who has been inactive for twelve months moves to emeritus,
which is not a judgment and is reversible on request.

## Licensing

Apache-2.0 for the code. Bundled data sets keep their upstream licences
and are attributed in [NOTICE](NOTICE); the two currently bundled are
CC BY 4.0.

A contribution is accepted under Apache-2.0. Contributing data derived
from a differently licensed source requires the licence to be compatible
and recorded in `NOTICE` in the same pull request.

## What is not decided yet

Named, so nobody assumes otherwise:

- **Who hosts this after the founding institutions.** No foundation, no
  fiscal host, no continuity plan. This is the single largest open
  question.
- **Who owns the non-code assets.** The pattern sets, the code books and
  any benchmark workloads are measuring instruments; a member who cannot
  use them cannot check another member's records. The licences allow use;
  stewardship is unassigned.
- **Whether a contributor license agreement is needed** instead of the
  DCO. Currently DCO.
- **How a dispute between maintainers is resolved** when consensus fails
  and escalation does not settle it.
- **How the release signing key is held**, rotated and revoked, and what a
  downstream reader checks.

Each of these is a decision the project will have to make. Writing them
down as open is more useful than leaving them implicit.
