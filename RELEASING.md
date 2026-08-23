# Releasing

## Cadence

Minor releases quarterly, on a schedule rather than when something is
ready, so downstream can plan. Patch releases whenever a fix warrants one.
A security fix ships as soon as it is ready and is announced through the
channels in [SECURITY.md](SECURITY.md).

The five packages version together. A user who installs `parapet-scope`
0.3.1 and `parapet-record` 0.3.1 gets a combination that was tested; mixed
versions are not.

## Support window

Pre-1.0, only the latest release gets fixes.

From 1.0: the current minor and the one before it, for six months after
the newer one ships. A major version keeps its last minor alive for twelve
months.

## Registry

PyPI, published by the release workflow through a trusted publisher. No
long-lived API token exists, so there is none to steal.

Every release also gets a Zenodo DOI, so citations and the References
Cited entry in a proposal point at a stable identifier rather than a bare
URL.

## Versioning

Semantic versioning, with one addition that follows from what this project
ships:

- **Changing a pattern definition** is a minor version at least. It
  changes what an existing user's queue looks like.
- **Removing a pattern** is a major version. Deprecate for one minor
  version first.
- **A breaking change to the record schema** is a major version of every
  package, because the schema is what makes them compose.

## Cutting a release

1. `make check` must be green.
2. Update `CHANGELOG.md`: move `Unreleased` into a dated version, and
   write it for someone deciding whether to upgrade.
3. Bump the version in all five `pyproject.toml` files and the five
   `__init__.py` files. They must agree.
4. Update `CITATION.cff` if authorship changed.
5. Open a release pull request. Two maintainer approvals, per
   [GOVERNANCE.md](GOVERNANCE.md).
6. Tag on `main`, signed:

   ```bash
   git tag -s v0.2.0 -m "v0.2.0"
   git push origin v0.2.0
   ```

7. The release workflow builds every package, generates an SBOM, attests
   build provenance, publishes to PyPI and creates the GitHub release.
   Nothing is built on a maintainer's machine.
8. Check the Zenodo deposition and copy the DOI into `CITATION.cff` for
   the next release.

## After a release

Watch the issue tracker for a week. A release that breaks an install is
worse than a late release; yank from PyPI and ship a patch rather than
leaving it.

## Yanking

Yank a release that cannot be installed, that ships a vulnerability, or
that produces wrong output silently. Say why in `CHANGELOG.md`. Yanking
does not remove the artifact, so anyone pinned to it keeps working while
new installs move on.
