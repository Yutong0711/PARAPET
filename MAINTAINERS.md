# Maintainers

This list is authoritative. [GOVERNANCE.md](GOVERNANCE.md) says what a
maintainer may do and how the list changes.

| Name | GitHub | Areas | Schema owner |
| --- | --- | --- | --- |
| Yutong Zhao | [@Yutong0711](https://github.com/Yutong0711) | all packages | yes |

One maintainer is not a governance model, it is a starting point, and it
is the single largest risk to this project's continuity. Everything in
[GOVERNANCE.md](GOVERNANCE.md) that says "two approvals" is aspirational
until this table has a second row.

## Areas

An area is what a maintainer is expected to review, not what they are
allowed to. Any maintainer may review anything.

The **schema owner** is accountable for `parapet-record`. Every component
writes into one schema, so an uncoordinated change there breaks all of
them, and a major version bump has to be somebody's decision rather than a
side effect.

## Emeritus

Nobody yet. A maintainer inactive for twelve months moves here. It is not
a judgment and it is reversible on request.

## Becoming a maintainer

Sustained contribution over months, then explicit consensus of the current
maintainers. Nobody has to ask; if the work is there, someone will
propose it.

Where "sustained" is doing work the project needs: reviewing pull
requests, answering issues, keeping the corpus validation honest. Commit
count is not the measure.
