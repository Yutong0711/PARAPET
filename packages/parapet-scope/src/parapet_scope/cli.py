"""``parapet-scope``: how wide is this change, and how should it be reviewed.

Three commands:

``analyze``  classify one revision and write the review-cost record
``dsm``      print the design structure matrix of a checkout or a revision
``batch``    classify a range of revisions, for a survey of a repository
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .classify import analyse
from .dsm import build_diff_dsm, build_dsm
from .gitsource import GitError, load_revision, resolve, issue_keys
from .record import write_record


def _read_local_tree(root: Path, suffix: str = ".java") -> dict:
    return {str(path.relative_to(root)).replace("\\", "/"):
            path.read_text(encoding="utf-8", errors="replace")
            for path in root.rglob(f"*{suffix}")}


def _add_repo_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--scope", default="neighbourhood",
                        choices=("changed", "neighbourhood", "full"),
                        help="how much of the tree to read; 'full' is the most "
                             "accurate and the slowest")
    parser.add_argument("--neighbourhood", type=int, default=1,
                        help="how far to reach around the changed files")


def cmd_analyze(args) -> int:
    try:
        revision = load_revision(args.repo, args.commit, args.base, args.scope)
    except GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not revision.changed:
        print(f"{revision.short} changed no .java files", file=sys.stderr)
        return 1

    diff = build_diff_dsm(revision.before, revision.after, revision.changed,
                          change_ref=revision.short,
                          neighbourhood=args.neighbourhood)
    verdict = analyse(diff, revision.before, revision.after)

    if args.record:
        path = write_record(args.record, verdict, diff, revision,
                            command=" ".join(sys.argv))
        print(f"wrote {path}", file=sys.stderr)

    if args.json:
        payload = {"tool": "parapet-scope", "version": __version__,
                   "commit": revision.commit, "base": revision.base,
                   "subject": revision.subject,
                   "issues": issue_keys(args.repo, revision.commit),
                   "verdict": verdict.to_dict(), "diff_dsm": diff.to_dict()}
        print(json.dumps(payload, indent=2))
    else:
        print(f"{revision.short}  {revision.subject}")
        print(verdict.advice())
        for note in verdict.notes:
            print(f"  note: {note}")
        if args.show_dsm:
            print()
            print(diff.render())
    return 0


def cmd_dsm(args) -> int:
    if args.commit:
        try:
            revision = load_revision(args.repo, args.commit, args.base, "full")
        except GitError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        sources = revision.after
        label = revision.short
    else:
        root = Path(args.repo)
        sources = _read_local_tree(root)
        label = str(root)
    if not sources:
        print(f"no .java files found in {args.repo}", file=sys.stderr)
        return 1

    dsm = build_dsm(sources)
    if args.json:
        print(json.dumps({"label": label, "summary": dsm.summary(),
                          "files": list(dsm.files),
                          "edges": [list(edge) for edge in sorted(dsm.edges)],
                          "unresolved": [list(item) for item in dsm.unresolved]},
                         indent=2))
        return 0
    print(f"{label}: {dsm.summary()}")
    print(dsm.render(args.max_files))
    if dsm.unresolved and args.verbose:
        print(f"\n{len(dsm.unresolved)} unresolved reference(s):")
        for path, name in dsm.unresolved[:20]:
            print(f"  {path}: {name}")
    return 0


def cmd_batch(args) -> int:
    from .gitsource import _git
    try:
        output = _git(args.repo, "log", "--format=%H", f"-{args.limit}",
                      args.revision_range)
    except GitError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    commits = [line.strip() for line in output.splitlines() if line.strip()]
    rows = []
    for index, commit in enumerate(commits, start=1):
        try:
            revision = load_revision(args.repo, commit, None, args.scope)
        except GitError:
            continue
        if not revision.changed:
            continue
        diff = build_diff_dsm(revision.before, revision.after, revision.changed,
                              change_ref=commit[:12],
                              neighbourhood=args.neighbourhood)
        verdict = analyse(diff, revision.before, revision.after)
        rows.append({"commit": commit, "subject": revision.subject,
                     **verdict.to_dict()})
        if not args.json:
            print(f"  {commit[:12]}  {verdict.scope:<13} "
                  f"{verdict.design_pattern or '':<28} "
                  f"{verdict.n_production_files:>3}p {verdict.n_test_files:>2}t  "
                  f"{revision.subject[:50]}")
        if index % 50 == 0:
            print(f"  ... {index}/{len(commits)}", file=sys.stderr)

    if args.json:
        print(json.dumps({"tool": "parapet-scope", "version": __version__,
                          "n_revisions": len(rows), "revisions": rows}, indent=2))
    else:
        design = sum(1 for row in rows if row["scope"] == "design-level")
        with_tests = sum(1 for row in rows if row["n_test_files"])
        total = len(rows) or 1
        print(f"\n{len(rows)} revision(s): {design} design-level "
              f"({design / total:.0%}), {with_tests} touched tests "
              f"({with_tests / total:.0%})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parapet-scope",
        description="Classify how wide a change is and how to review it.")
    parser.add_argument("--version", action="version",
                        version=f"parapet-scope {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="classify one revision")
    analyze.add_argument("--commit", default="HEAD")
    analyze.add_argument("--base", default=None,
                         help="compare against this revision instead of the parent")
    analyze.add_argument("--json", action="store_true")
    analyze.add_argument("--show-dsm", action="store_true")
    analyze.add_argument("--record", type=Path, default=None,
                         help="write the review-cost record here")
    _add_repo_args(analyze)
    analyze.set_defaults(func=cmd_analyze)

    dsm = sub.add_parser("dsm", help="print a design structure matrix")
    dsm.add_argument("--commit", default=None,
                     help="a revision; omit to read the working tree")
    dsm.add_argument("--base", default=None)
    dsm.add_argument("--json", action="store_true")
    dsm.add_argument("--verbose", action="store_true")
    dsm.add_argument("--max-files", type=int, default=20)
    _add_repo_args(dsm)
    dsm.set_defaults(func=cmd_dsm)

    batch = sub.add_parser("batch", help="classify a range of revisions")
    batch.add_argument("revision_range", nargs="?", default="HEAD")
    batch.add_argument("--limit", type=int, default=50)
    batch.add_argument("--json", action="store_true")
    _add_repo_args(batch)
    batch.set_defaults(func=cmd_batch)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
