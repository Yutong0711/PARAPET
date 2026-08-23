"""``parapet-attrib``: where in the architecture did the added cost land.

Four commands:

``diff``     compare two profiles and attribute the change
``space``    print the region of the architecture around a method
``graph``    build or import a call graph and describe it
``hotspots`` the most expensive methods near a change, from one profile
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from . import __version__
from .attribute import attribute, hotspots
from .graphio import load_graph, save_graph
from .profiles import compare, load_profile
from .record import write_record
from .space import build_space


def _read_methods(value: Optional[str]) -> List[str]:
    """A comma-separated list, or a file with one method per line."""
    if not value:
        return []
    path = Path(value)
    if path.exists():
        return [line.strip() for line in
                path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")]
    return [item.strip() for item in value.split(",") if item.strip()]


def _add_graph_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--graph", type=Path, default=None,
                        help="a call graph file; omit to build one from --source")
    parser.add_argument("--graph-format", default="auto",
                        choices=("auto", "csv", "json", "java-callgraph",
                                 "understand"))
    parser.add_argument("--source", type=Path, default=None,
                        help="a Java source tree to build a call graph from")


def _get_graph(args):
    if args.graph:
        return load_graph(args.graph, args.graph_format)
    if args.source:
        from .javacalls import build_call_graph
        from .space import CallGraph
        root = Path(args.source)
        sources = {str(p.relative_to(root)).replace("\\", "/"):
                   p.read_text(encoding="utf-8", errors="replace")
                   for p in root.rglob("*.java")}
        if not sources:
            raise SystemExit(f"no .java files under {root}")
        java_graph = build_call_graph(sources)
        graph = CallGraph.from_edges(java_graph.to_edge_list(),
                                     java_graph.methods.keys())
        print(f"built a call graph from {len(sources)} file(s): "
              f"{graph.summary()}", file=sys.stderr)
        if java_graph.unresolved:
            print(f"  {len(java_graph.unresolved)} call site(s) unresolved",
                  file=sys.stderr)
        return graph
    raise SystemExit("pass --graph or --source")


def cmd_diff(args) -> int:
    graph = _get_graph(args)
    before = load_profile(args.before, args.profile_format, label="before")
    after = load_profile(args.after, args.profile_format, label="after")
    changed = _read_methods(args.changed)
    if not changed:
        print("error: --changed is required; give the methods the change "
              "touched", file=sys.stderr)
        return 1

    result = attribute(graph, before, after, changed, metric=args.metric,
                       max_layers=args.max_layers, noise_floor=args.noise_floor,
                       change_ref=args.change_ref or "")

    if args.record:
        path = write_record(args.record, result, before, after,
                            command=" ".join(sys.argv))
        print(f"wrote {path}", file=sys.stderr)

    if args.json:
        print(json.dumps({"tool": "parapet-attrib", "version": __version__,
                          "before": before.summary(), "after": after.summary(),
                          "attribution": result.to_dict()}, indent=2))
    else:
        print(result.summary())
    if args.fail_on_regression and result.total_delta > 0:
        return 2
    return 0


def cmd_space(args) -> int:
    graph = _get_graph(args)
    if args.method not in graph:
        matches = [m for m in graph.methods if args.method in m]
        print(f"error: {args.method!r} is not in the call graph", file=sys.stderr)
        if matches:
            print("did you mean one of:", file=sys.stderr)
            for match in matches[:10]:
                print(f"  {match}", file=sys.stderr)
        return 1
    space = build_space(graph, args.method, args.max_layers)
    if args.json:
        print(json.dumps(space.to_dict(), indent=2))
    else:
        print(f"space of {args.method}: {space.size} method(s) of {len(graph)} "
              f"({space.size / max(1, len(graph)):.0%} of the system)")
        print(space.render(args.max_per_layer))
    return 0


def cmd_graph(args) -> int:
    graph = _get_graph(args)
    if args.output:
        save_graph(graph, args.output)
        print(f"wrote {args.output}", file=sys.stderr)
    if args.json:
        print(json.dumps(graph.summary(), indent=2))
    else:
        print(graph.summary())
        if args.list:
            for method in graph.methods[: args.list]:
                print(f"  {method}")
    return 0


def cmd_hotspots(args) -> int:
    graph = _get_graph(args)
    profile = load_profile(args.profile, args.profile_format)
    changed = _read_methods(args.changed)
    rows = hotspots(profile, graph, changed, args.metric, args.limit)
    if args.json:
        print(json.dumps({"metric": args.metric, "hotspots": rows}, indent=2))
    else:
        print(f"most expensive methods near the change ({args.metric}):")
        for row in rows:
            print(f"  {row[args.metric]:>12.4g}  {row['method']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parapet-attrib",
        description="Say where in the architecture a cost change landed.")
    parser.add_argument("--version", action="version",
                        version=f"parapet-attrib {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    diff = sub.add_parser("diff", help="attribute the change between two profiles")
    diff.add_argument("--before", required=True, type=Path)
    diff.add_argument("--after", required=True, type=Path)
    diff.add_argument("--changed", required=True,
                      help="comma-separated methods, or a file of them")
    diff.add_argument("--profile-format", default="auto",
                      choices=("auto", "csv", "json", "jfr", "jmh"))
    diff.add_argument("--metric", default="time", choices=("time", "own_time", "count"))
    diff.add_argument("--max-layers", type=int, default=0,
                      help="0 means an unbounded space")
    diff.add_argument("--noise-floor", type=float, default=0.01,
                      help="ignore relative changes smaller than this")
    diff.add_argument("--change-ref", default=None)
    diff.add_argument("--record", type=Path, default=None)
    diff.add_argument("--json", action="store_true")
    diff.add_argument("--fail-on-regression", action="store_true",
                      help="exit 2 when total cost rose, for CI gates")
    _add_graph_args(diff)
    diff.set_defaults(func=cmd_diff)

    space = sub.add_parser("space", help="show the region around a method")
    space.add_argument("method")
    space.add_argument("--max-layers", type=int, default=0)
    space.add_argument("--max-per-layer", type=int, default=6)
    space.add_argument("--json", action="store_true")
    _add_graph_args(space)
    space.set_defaults(func=cmd_space)

    graph = sub.add_parser("graph", help="build, convert or describe a call graph")
    graph.add_argument("--output", type=Path, default=None)
    graph.add_argument("--list", type=int, default=0)
    graph.add_argument("--json", action="store_true")
    _add_graph_args(graph)
    graph.set_defaults(func=cmd_graph)

    hot = sub.add_parser("hotspots", help="expensive methods near a change")
    hot.add_argument("--profile", required=True, type=Path)
    hot.add_argument("--changed", required=True)
    hot.add_argument("--profile-format", default="auto",
                     choices=("auto", "csv", "json", "jfr", "jmh"))
    hot.add_argument("--metric", default="time", choices=("time", "own_time", "count"))
    hot.add_argument("--limit", type=int, default=10)
    hot.add_argument("--json", action="store_true")
    _add_graph_args(hot)
    hot.set_defaults(func=cmd_hotspots)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
