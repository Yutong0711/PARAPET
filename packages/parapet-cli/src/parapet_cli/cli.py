"""``parapet``: the one command that produces a hardening record.

    parapet init                 write a starter service budget
    parapet run                  chain the components into one record
    parapet show <record.json>   read a record back
    parapet doctor               what is installed and what it can do
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__
from .budget import DEFAULT_FILENAME, describe, load_budget, write_budget_template
from .pipeline import run_pipeline

COMPONENTS = ("parapet_record", "parapet_triage", "parapet_scope",
              "parapet_attrib")


def _methods(value: Optional[str]) -> List[str]:
    if not value:
        return []
    path = Path(value)
    if path.exists():
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")]
    return [item.strip() for item in value.split(",") if item.strip()]


def cmd_init(args) -> int:
    path = write_budget_template(args.path, args.project)
    print(f"wrote {path}")
    print("\nEdit it before committing. Two fields decide whether it is worth "
          "anything:")
    print("  authority  who may change these limits, and on what evidence")
    print("  workloads  what a cost claim is measured on; without these a "
          "limit cannot be checked")
    return 0


def cmd_run(args) -> int:
    result = run_pipeline(
        out=args.out,
        issues=args.issues, issue_format=args.issue_format,
        pattern_set=args.patterns,
        repo=args.repo, commit=args.commit, base=args.base,
        scope_depth=args.scope,
        before_profile=args.before, after_profile=args.after,
        profile_format=args.profile_format,
        graph=args.graph, source=args.source,
        changed_methods=_methods(args.changed_methods),
        metric=args.metric,
        budget_path=args.budget,
        record_id=args.record_id or (args.commit if args.repo else "record"),
        command=" ".join(sys.argv))

    if args.json:
        print(json.dumps({"verdict": result.verdict,
                          "record": str(result.record_path),
                          "stages": [{"name": s.name, "ran": s.ran,
                                      "detail": s.detail} for s in result.stages],
                          "warnings": result.warnings}, indent=2))
    else:
        print(result.summary())

    if args.fail_on_overrun and result.verdict == "overrun":
        return 2
    if args.fail_unless_admitted and result.verdict != "admitted":
        return 3
    return 0


def cmd_show(args) -> int:
    payload = json.loads(Path(args.record).read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    exposure = payload.get("exposure") or {}
    review = payload.get("review_cost") or {}
    attribution = payload.get("attribution") or {}
    print(f"record {payload.get('record_id', '?')}  "
          f"[{payload.get('verdict', 'unscored')}]")
    if exposure:
        print(f"  exposure: {exposure.get('identifier')} "
              f"({exposure.get('kind')}, {exposure.get('cwe') or 'no CWE'})")
        print(f"    {(exposure.get('title') or exposure.get('text', ''))[:100]}")
        print(f"    reproducer: {exposure.get('reproducer') or 'none recorded'}")
        if exposure.get("labels"):
            print(f"    matched: {', '.join(exposure['labels'][:6])}")
    if review:
        print(f"  review cost: {review.get('scope')}"
              + (f", {review.get('design_pattern')}"
                 if review.get("design_pattern") else ""))
        print(f"    {review.get('n_production_files')} production file(s), "
              f"{review.get('n_test_files')} test file(s)")
        if review.get("cochange_patterns"):
            print(f"    tests: {', '.join(review['cochange_patterns'])}")
    for cost in payload.get("costs", []):
        interval = ("no interval" if cost.get("interval_low") is None
                    else f"[{cost['interval_low']:.4g}, {cost['interval_high']:.4g}]")
        print(f"  cost: {cost['dimension']} {cost['value']:.4g}{cost['unit']} "
              f"(baseline {cost.get('baseline')}, {interval}) "
              f"on {cost.get('workload')}")
    if attribution:
        print(f"  the cost landed: {attribution.get('where')}")
        for pattern in attribution.get("patterns", [])[:3]:
            print(f"    {pattern['pattern']}: {pattern['reason']}")
    for check in payload.get("budget_checks", []):
        verdict = "fits" if check.get("fits") else "OVER"
        print(f"  budget {check['dimension']:<8} limit {check['limit']:<8} "
              f"{verdict}  {check.get('reason', '')}")
    for warning in payload.get("warnings", []):
        print(f"  warning: {warning}")
    return 0


def cmd_doctor(args) -> int:
    import importlib
    print(f"parapet {__version__}")
    missing = []
    for name in COMPONENTS:
        try:
            module = importlib.import_module(name)
            print(f"  {name.replace('_', '-'):<16} "
                  f"{getattr(module, '__version__', '?')}")
        except ImportError:
            missing.append(name)
            print(f"  {name.replace('_', '-'):<16} not installed")
    if missing:
        print("\nInstall what you need:")
        print("  pip install " + " ".join(n.replace("_", "-") for n in missing))
    print("\nWhat each stage needs:")
    print("  triage  --issues        a CSV, JSON, OSV or GitHub export")
    print("  scope   --repo          a git checkout with Java sources")
    print("  attrib  --before/--after and --graph or --source")
    print("  budget  --budget        a service budget file "
          f"(parapet init writes one: {DEFAULT_FILENAME})")

    if args.budget:
        try:
            print()
            print(describe(load_budget(args.budget)))
        except (ValueError, RuntimeError) as exc:
            print(f"\nbudget {args.budget}: {exc}")
            return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parapet",
        description="Turn an exposure into a reviewable decision.")
    parser.add_argument("--version", action="version", version=f"parapet {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="write a starter service budget")
    init.add_argument("--path", type=Path, default=Path(DEFAULT_FILENAME))
    init.add_argument("--project", default="my-project")
    init.set_defaults(func=cmd_init)

    run = sub.add_parser("run", help="chain the components into one record")
    run.add_argument("--out", type=Path, default=Path("records"))
    run.add_argument("--record-id", default=None)
    run.add_argument("--issues", type=Path, default=None)
    run.add_argument("--issue-format", default="auto",
                     choices=("auto", "csv", "json", "osv", "github", "text"))
    run.add_argument("--patterns", default="performance")
    run.add_argument("--repo", type=Path, default=None)
    run.add_argument("--commit", default="HEAD")
    run.add_argument("--base", default=None)
    run.add_argument("--scope", default="neighbourhood",
                     choices=("changed", "neighbourhood", "full"))
    run.add_argument("--before", type=Path, default=None)
    run.add_argument("--after", type=Path, default=None)
    run.add_argument("--profile-format", default="auto",
                     choices=("auto", "csv", "json", "jfr", "jmh"))
    run.add_argument("--graph", type=Path, default=None)
    run.add_argument("--source", type=Path, default=None)
    run.add_argument("--changed-methods", default=None)
    run.add_argument("--metric", default="time",
                     choices=("time", "own_time", "count"))
    run.add_argument("--budget", type=Path, default=None)
    run.add_argument("--json", action="store_true")
    run.add_argument("--fail-on-overrun", action="store_true",
                     help="exit 2 when the measured cost exceeds the budget")
    run.add_argument("--fail-unless-admitted", action="store_true",
                     help="exit 3 unless the record reaches a clean verdict")
    run.set_defaults(func=cmd_run)

    show = sub.add_parser("show", help="read a record back")
    show.add_argument("record", type=Path)
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_show)

    doctor = sub.add_parser("doctor", help="what is installed and what it needs")
    doctor.add_argument("--budget", type=Path, default=None)
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
