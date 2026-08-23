"""``parapet-triage``: route issue reports and advisories.

Four commands:

``classify``   score reports against a pattern set and write records
``explain``    show why one report scored the way it did
``patterns``   list a pattern set and how each entry compiled
``doctor``     report what this installation can and cannot decide

Everything writes JSON when asked and a table when not, so the same
command serves a human at a terminal and a job in CI.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .classify import Triager
from .dsl import compile_set
from .patterns import BUILTIN_SETS, load_pattern_set
from .sources import load_reports
from .text import backend_report, get_backend


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--patterns", default="performance",
                        help="built-in set name or a path to a YAML set "
                             f"(built-in: {', '.join(sorted(BUILTIN_SETS))})")
    parser.add_argument("--backend", default="simple", choices=("simple", "spacy"),
                        help="simple needs no models; spacy adds POS and NER")
    parser.add_argument("--spacy-model", default="en_core_web_sm")
    parser.add_argument("--sentence-threshold", type=float, default=None)
    parser.add_argument("--issue-threshold", type=float, default=None)


def _build_triager(args) -> Triager:
    kwargs = {}
    if args.sentence_threshold is not None:
        kwargs["sentence_threshold"] = args.sentence_threshold
    if args.issue_threshold is not None:
        kwargs["issue_threshold"] = args.issue_threshold
    return Triager(pattern_set=load_pattern_set(args.patterns),
                   backend=args.backend, spacy_model=args.spacy_model, **kwargs)


# ---------------------------------------------------------------------------
# classify
# ---------------------------------------------------------------------------

def cmd_classify(args) -> int:
    reports = load_reports(args.input, args.format)
    if not reports:
        print(f"no reports found in {args.input}", file=sys.stderr)
        return 1
    triager = _build_triager(args)
    verdicts = [triager.classify_text(report.text, report.identifier)
                for report in reports]

    if args.only_matches:
        shown = [v for v in verdicts if v.is_match]
    else:
        shown = verdicts

    if args.record:
        from .record import build_records
        path = Path(args.record)
        build_records(reports, verdicts, triager, path,
                      command=" ".join(sys.argv))
        print(f"wrote {len(verdicts)} record(s) to {path}", file=sys.stderr)

    if args.json:
        payload = {"tool": "parapet-triage", "version": __version__,
                   "config": triager.report(),
                   "results": [v.to_dict() for v in shown]}
        target = Path(args.output) if args.output else None
        text = json.dumps(payload, indent=2)
        if target:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(f"wrote {target}", file=sys.stderr)
        else:
            print(text)
    else:
        matched = sum(1 for v in verdicts if v.is_match)
        print(f"{matched}/{len(verdicts)} report(s) matched "
              f"[{triager.pattern_set.set_id}, {triager.backend.name} backend]")
        width = max((len(v.identifier) for v in shown), default=8)
        for verdict in shown:
            mark = "MATCH" if verdict.is_match else "  -  "
            names = ", ".join(verdict.patterns[:4])
            print(f"  {mark}  {verdict.identifier:<{width}}  "
                  f"{verdict.score:5.2f}  {names}")

    if args.fail_on_match and any(v.is_match for v in verdicts):
        return 2
    return 0


# ---------------------------------------------------------------------------
# explain
# ---------------------------------------------------------------------------

def cmd_explain(args) -> int:
    reports = load_reports(args.input, args.format)
    wanted = [r for r in reports if not args.id or r.identifier == args.id]
    if not wanted:
        print(f"no report with id {args.id!r} in {args.input}", file=sys.stderr)
        return 1
    triager = _build_triager(args)
    for report in wanted[: args.limit]:
        verdict = triager.classify_text(report.text, report.identifier)
        print(verdict.explain(limit=args.sentences))
        print()
    return 0


# ---------------------------------------------------------------------------
# patterns
# ---------------------------------------------------------------------------

def cmd_patterns(args) -> int:
    pattern_set = load_pattern_set(args.patterns)
    compiled, report = compile_set(pattern_set.patterns)

    if args.json:
        print(json.dumps({"set_id": pattern_set.set_id,
                          "categories": pattern_set.categories(),
                          "report": report,
                          "patterns": [{"id": c.pattern_id, "name": c.name,
                                        "category": c.category,
                                        "compiled": c.describe(),
                                        "repairs": c.repairs,
                                        "needs_pos": c.needs_pos}
                                       for c in compiled]}, indent=2))
        return 0

    print(f"{pattern_set.set_id}: {len(pattern_set)} patterns "
          f"{pattern_set.categories()}")
    if pattern_set.source:
        print(f"  source: {pattern_set.source}")
    print(f"  usable {report['n_usable']}, repaired {report['n_repaired']}, "
          f"need a tagger {report['n_need_pos']}")
    for item in compiled:
        if args.name and args.name not in item.name:
            continue
        flags = []
        if item.repairs:
            flags.append("repaired")
        if item.needs_pos:
            flags.append("needs-tagger")
        suffix = f"  [{', '.join(flags)}]" if flags else ""
        print(f"\n  {item.pattern_id} {item.name} ({item.category}){suffix}")
        if args.verbose:
            print(f"    definition: {item.definition}")
            print(f"    compiled:   {item.describe()}")
            for repair in item.repairs:
                print(f"    repair:     {repair}")
    if report["repaired"] and not args.verbose:
        print(f"\n{report['n_repaired']} pattern(s) needed repair; "
              "re-run with --verbose to see what changed")
    return 0


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args) -> int:
    print(f"parapet-triage {__version__}")
    for name in sorted(BUILTIN_SETS):
        try:
            pattern_set = load_pattern_set(name)
            _compiled, report = compile_set(pattern_set.patterns)
            print(f"  pattern set {name:<12} {len(pattern_set):>3} patterns, "
                  f"{report['n_usable']} usable, {report['n_repaired']} repaired")
        except Exception as exc:  # noqa: BLE001 - a doctor reports, never raises
            print(f"  pattern set {name:<12} FAILED: {exc}")

    for backend_name in ("simple", "spacy"):
        try:
            backend = get_backend(backend_name, args.spacy_model)
        except RuntimeError as exc:
            print(f"  backend {backend_name:<8} unavailable: "
                  f"{str(exc).splitlines()[0]}")
            continue
        info = backend_report(backend)
        degraded = info["degraded_patterns"]
        print(f"  backend {backend_name:<8} available "
              f"(POS: {info['part_of_speech']}, NER: {info['named_entities']})")
        if degraded:
            print(f"           {len(degraded)} pattern(s) run degraded: "
                  f"{', '.join(degraded)}")
    print("\nThe simple backend is enough for most patterns. Install the "
          "'nlp' extra only if the degraded list matters for your set.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parapet-triage",
        description="Route issue reports and advisories by what they describe.")
    parser.add_argument("--version", action="version",
                        version=f"parapet-triage {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    classify = sub.add_parser("classify", help="score reports against a set")
    classify.add_argument("input", type=Path)
    classify.add_argument("--format", default="auto",
                          choices=("auto", "csv", "json", "osv", "github", "text"))
    classify.add_argument("--json", action="store_true")
    classify.add_argument("--output", type=Path, default=None)
    classify.add_argument("--record", type=Path, default=None,
                          help="also write hardening records to this directory")
    classify.add_argument("--only-matches", action="store_true")
    classify.add_argument("--fail-on-match", action="store_true",
                          help="exit 2 when anything matches, for CI gates")
    _add_common(classify)
    classify.set_defaults(func=cmd_classify)

    explain = sub.add_parser("explain", help="show why a report scored as it did")
    explain.add_argument("input", type=Path)
    explain.add_argument("--id", default=None)
    explain.add_argument("--format", default="auto",
                         choices=("auto", "csv", "json", "osv", "github", "text"))
    explain.add_argument("--limit", type=int, default=5)
    explain.add_argument("--sentences", type=int, default=3)
    _add_common(explain)
    explain.set_defaults(func=cmd_explain)

    patterns = sub.add_parser("patterns", help="list a pattern set")
    patterns.add_argument("--name", default=None, help="filter by substring")
    patterns.add_argument("--verbose", action="store_true")
    patterns.add_argument("--json", action="store_true")
    _add_common(patterns)
    patterns.set_defaults(func=cmd_patterns)

    doctor = sub.add_parser("doctor", help="check this installation")
    doctor.add_argument("--spacy-model", default="en_core_web_sm")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
