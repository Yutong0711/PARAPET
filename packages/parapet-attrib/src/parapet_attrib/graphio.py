"""Reading and writing call graphs.

The graph is an edge list, so any tool that can name a caller and a callee
can feed this one. Four formats are recognised, covering the free static
analysers, the commercial one the original study used, and the plain CSV
everything else can export.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .space import CallGraph

PathLike = Union[str, Path]

_JAVA_CALLGRAPH = re.compile(r"^M:([^\s]+)\s+\((?:[A-Z]+\))?([^\s]+)\s*$")


def from_csv(path: PathLike, caller: str = "caller",
             callee: str = "callee") -> CallGraph:
    """Two columns. A row with a caller and no callee declares a leaf."""
    graph = CallGraph()
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = {str(name).lower().strip(): name
                  for name in (reader.fieldnames or [])}
        caller_key = fields.get(caller) or fields.get("from") or fields.get("source")
        callee_key = fields.get(callee) or fields.get("to") or fields.get("target")
        if caller_key is None:
            raise ValueError(
                f"{path} has columns {list(fields)}; expected a {caller!r} column")
        for row in reader:
            source = str(row.get(caller_key) or "").strip()
            target = str(row.get(callee_key) or "").strip() if callee_key else ""
            if source and target:
                graph.add_call(source, target)
            elif source:
                graph.add_method(source)
    return graph


def from_json(path: PathLike) -> CallGraph:
    """``{"methods": [...], "edges": [[caller, callee], ...]}``."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return CallGraph.from_edges(payload.get("edges", []),
                                payload.get("methods", []))


def from_java_callgraph(path: PathLike) -> CallGraph:
    """``java-callgraph`` output: ``M:a.Foo:bar (M)b.Baz:qux``.

    A free static analyser that runs on a jar, so a project with a build
    but no commercial licence can still produce a graph. Class-level ``C:``
    lines are ignored; spaces are method-level.
    """
    graph = CallGraph()
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        match = _JAVA_CALLGRAPH.match(line.strip())
        if match:
            graph.add_call(_normalise(match.group(1)), _normalise(match.group(2)))
    return graph


def from_understand(path: PathLike) -> CallGraph:
    """Understand's dependency export, filtered to call references."""
    graph = CallGraph()
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = {str(name).lower().strip(): name
                  for name in (reader.fieldnames or [])}
        from_key = next((fields[k] for k in ("from entity", "from", "caller")
                         if k in fields), None)
        to_key = next((fields[k] for k in ("to entity", "to", "callee")
                       if k in fields), None)
        kind_key = next((fields[k] for k in ("kind", "reference", "references")
                         if k in fields), None)
        if from_key is None or to_key is None:
            raise ValueError(
                f"{path} has columns {list(fields)}; expected 'From Entity' "
                "and 'To Entity'")
        for row in reader:
            if kind_key and row.get(kind_key) and \
                    "call" not in str(row[kind_key]).lower():
                continue
            source = str(row.get(from_key) or "").strip()
            target = str(row.get(to_key) or "").strip()
            if source and target:
                graph.add_call(_normalise(source), _normalise(target))
    return graph


def _normalise(method: str) -> str:
    """``a.Foo:bar`` and ``a.Foo.bar`` both become ``a.Foo#bar``.

    One spelling for a method means a profile and a graph from different
    tools can be joined without the caller doing string surgery.
    """
    method = method.strip()
    if "#" in method:
        return method
    if ":" in method:
        owner, _, name = method.rpartition(":")
        return f"{owner}#{name}"
    if "." in method:
        owner, _, name = method.rpartition(".")
        return f"{owner}#{name}"
    return method


LOADERS = {"csv": from_csv, "json": from_json,
           "java-callgraph": from_java_callgraph, "understand": from_understand}


def detect_format(path: PathLike) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    head = ""
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            head = "".join(next(handle, "") for _ in range(5))
    except OSError:
        pass
    if head.startswith(("M:", "C:")) or "\nM:" in head:
        return "java-callgraph"
    if "from entity" in head.lower():
        return "understand"
    return "csv"


def load_graph(path: PathLike, fmt: str = "auto") -> CallGraph:
    chosen = detect_format(path) if fmt == "auto" else fmt
    if chosen not in LOADERS:
        raise ValueError(f"unknown graph format {chosen!r}; expected "
                         f"{sorted(LOADERS)} or 'auto'")
    return LOADERS[chosen](path)


def save_graph(graph: CallGraph, path: PathLike) -> Path:
    """Write the canonical JSON form."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    edges = [[caller, callee] for caller in graph.methods
             for callee in sorted(graph.callees(caller))]
    path.write_text(json.dumps({"methods": list(graph.methods), "edges": edges},
                               indent=2), encoding="utf-8")
    return path
