"""A method call graph read out of Java source, without a build.

The published study used Understand. This module gets a usable call graph
from the source text: it finds method declarations by brace depth and call
sites by pattern, then resolves each call site to a declared method where
it can.

What it resolves, in order of confidence:

* a call to a method declared in the same type;
* a call through a field or a local whose declared type is a type in this
  repository;
* a call through ``super`` or a constructor of a resolvable type;
* a call whose name is declared by exactly one type in the repository.

What it cannot resolve is recorded, not guessed. A call through an
interface reaches the interface's method, not the implementation a virtual
dispatch would pick, so a call graph from source is an over-approximation
upward and an under-approximation across implementations. For attributing
measured cost to a region of the architecture that is enough; for anything
that needs soundness it is not, and
``parapet-attrib import`` takes a graph from a real analyser instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+?)(\.\*)?\s*;", re.M)
_TYPE_DECL = re.compile(
    r"\b(?:public|protected|private|static|final|abstract|sealed|\s)*"
    r"(?:class|interface|enum|record)\s+(\w+)")
_METHOD_DECL = re.compile(
    r"^[ \t]*(?:@\w+(?:\([^)]*\))?[ \t]*)*"
    r"(?P<mods>(?:public|protected|private|static|final|abstract|synchronized|"
    r"native|strictfp|default|[ \t])*)"
    r"(?:<[^>]{0,80}>[ \t]*)?"
    r"(?P<ret>[\w.$<>\[\], \t?]+?)[ \t]+"
    r"(?P<name>\w+)[ \t]*\((?P<args>[^;{)]*)\)[ \t]*(?:throws [\w., \t]+)?[ \t]*\{",
    re.M)
_CONSTRUCTOR = re.compile(
    r"^[ \t]*(?:public|protected|private)?[ \t]*(?P<name>[A-Z]\w*)[ \t]*"
    r"\([^;{)]*\)[ \t]*(?:throws [\w., \t]+)?[ \t]*\{", re.M)
_CALL = re.compile(r"(?:(?P<recv>\w+)\s*\.\s*)?(?P<name>\w+)\s*\(")
_FIELD_DECL = re.compile(r"\b(?:private|protected|public|final|static|\s)*"
                         r"([A-Z]\w*)(?:<[^>]{0,60}>)?\s+(\w+)\s*[=;]")
_NEW = re.compile(r"\bnew\s+([A-Z]\w*)\s*\(")

# Not calls: control flow, and the assertion vocabulary of test frameworks
# that would otherwise look like a call to something in the project.
NOT_CALLS = {"if", "for", "while", "switch", "catch", "synchronized", "return",
             "throw", "new", "super", "this", "assert", "do", "else", "try"}


@dataclass
class MethodDecl:
    """One declared method, and the lines it occupies."""

    owner: str                 # qualified type name
    name: str
    start_line: int
    end_line: int
    path: str
    signature: str = ""

    @property
    def key(self) -> str:
        """``pkg.Type#method``, the identifier the graph uses."""
        return f"{self.owner}#{self.name}"

    def contains(self, line: int) -> bool:
        return self.start_line <= line <= self.end_line


@dataclass
class JavaCallGraph:
    """Methods and the calls between them."""

    methods: Dict[str, MethodDecl] = field(default_factory=dict)
    edges: Set[Tuple[str, str]] = field(default_factory=set)
    unresolved: List[Tuple[str, str]] = field(default_factory=list)

    def add_method(self, decl: MethodDecl) -> None:
        self.methods.setdefault(decl.key, decl)

    def add_call(self, caller: str, callee: str) -> None:
        if caller != callee:
            self.edges.add((caller, callee))

    def to_edge_list(self) -> List[Tuple[str, str]]:
        return sorted(self.edges)

    def summary(self) -> dict:
        return {"n_methods": len(self.methods), "n_calls": len(self.edges),
                "n_unresolved": len(self.unresolved)}

    def methods_in_file(self, path: str) -> List[MethodDecl]:
        return [decl for decl in self.methods.values() if decl.path == path]


def _blank_noise(source: str) -> str:
    """Replace comments, strings and chars with spaces, keeping offsets."""
    out, index, length = [], 0, len(source)
    while index < length:
        char = source[index]
        nxt = source[index + 1] if index + 1 < length else ""
        if char == "/" and nxt == "/":
            while index < length and source[index] != "\n":
                out.append(" ")
                index += 1
        elif char == "/" and nxt == "*":
            while index < length and not (source[index] == "*" and
                                          index + 1 < length and
                                          source[index + 1] == "/"):
                out.append("\n" if source[index] == "\n" else " ")
                index += 1
            out.append("  ")
            index += 2
        elif char in "\"'":
            quote = char
            out.append(" ")
            index += 1
            while index < length:
                if source[index] == "\\":
                    out.append("  ")
                    index += 2
                    continue
                if source[index] == quote:
                    out.append(" ")
                    index += 1
                    break
                out.append("\n" if source[index] == "\n" else " ")
                index += 1
        else:
            out.append(char)
            index += 1
    return "".join(out)


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _body_end(text: str, open_brace: int) -> int:
    """Offset just past the matching close brace."""
    depth, index, length = 0, open_brace, len(text)
    while index < length:
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return length


def _declared_types(cleaned: str) -> List[str]:
    return _TYPE_DECL.findall(cleaned)


def parse_file(path: str, source: str) -> Tuple[str, List[MethodDecl],
                                                Dict[str, str], List[str],
                                                Dict[str, Tuple[int, int]]]:
    """Methods, field types and imports of one file.

    Returns ``(package, methods, field_types, imports, bodies)`` where
    ``bodies`` maps a method key to the character offsets of its body.
    """
    cleaned = _blank_noise(source)
    package_match = _PACKAGE.search(cleaned)
    package = package_match.group(1) if package_match else ""
    types = _declared_types(cleaned)
    primary = types[0] if types else path.rsplit("/", 1)[-1][:-5]
    owner = f"{package}.{primary}" if package else primary

    imports = [dotted for dotted, _wild in _IMPORT.findall(cleaned)]
    field_types = {name: type_name
                   for type_name, name in _FIELD_DECL.findall(cleaned)}

    methods: List[MethodDecl] = []
    bodies: Dict[str, Tuple[int, int]] = {}
    for regex in (_METHOD_DECL, _CONSTRUCTOR):
        for match in regex.finditer(cleaned):
            name = match.group("name")
            if name in NOT_CALLS:
                continue
            returns = match.groupdict().get("ret", "")
            if returns and returns.strip() in NOT_CALLS:
                continue
            open_brace = cleaned.find("{", match.end() - 1)
            if open_brace == -1:
                continue
            end = _body_end(cleaned, open_brace)
            decl = MethodDecl(owner=owner, name=name,
                              start_line=_line_of(cleaned, match.start()),
                              end_line=_line_of(cleaned, end - 1), path=path,
                              signature=match.group(0).strip()[:120])
            if decl.key in bodies:
                continue           # an overload; the first body stands in
            methods.append(decl)
            bodies[decl.key] = (open_brace, end)
    return package, methods, field_types, imports, bodies


def build_call_graph(sources: Dict[str, str]) -> JavaCallGraph:
    """Build a call graph from ``{repo-relative path: source}``."""
    graph = JavaCallGraph()
    parsed: Dict[str, tuple] = {}
    simple_to_owner: Dict[str, List[str]] = {}
    method_owners: Dict[str, List[str]] = {}

    for path, source in sources.items():
        if not path.endswith(".java"):
            continue
        package, methods, fields, imports, bodies = parse_file(path, source)
        parsed[path] = (_blank_noise(source), package, methods, fields,
                        imports, bodies)
        for decl in methods:
            graph.add_method(decl)
            simple_to_owner.setdefault(decl.owner.rsplit(".", 1)[-1],
                                       []).append(decl.owner)
            method_owners.setdefault(decl.name, []).append(decl.owner)

    for path, (cleaned, package, methods, fields, imports, bodies) in parsed.items():
        import_simple = {dotted.rsplit(".", 1)[-1]: dotted for dotted in imports}
        for decl in methods:
            start, end = bodies[decl.key]
            body = cleaned[start:end]
            local_types = dict(fields)
            local_types.update({name: type_name for type_name, name
                                in _FIELD_DECL.findall(body)})
            for match in _CALL.finditer(body):
                name = match.group("name")
                if name in NOT_CALLS:
                    continue
                receiver = match.group("recv")
                target = _resolve(decl.owner, receiver, name, local_types,
                                  import_simple, simple_to_owner, method_owners,
                                  graph)
                if target is None:
                    graph.unresolved.append((decl.key, name))
                else:
                    graph.add_call(decl.key, target)
            for match in _NEW.finditer(body):
                type_name = match.group(1)
                owner = _owner_for(type_name, import_simple, simple_to_owner)
                if owner and f"{owner}#{type_name}" in graph.methods:
                    graph.add_call(decl.key, f"{owner}#{type_name}")
    return graph


def _owner_for(simple: str, import_simple: Dict[str, str],
               simple_to_owner: Dict[str, List[str]]) -> Optional[str]:
    dotted = import_simple.get(simple)
    if dotted:
        return dotted
    owners = simple_to_owner.get(simple, [])
    return owners[0] if len(set(owners)) == 1 else None


def _resolve(caller_owner: str, receiver: Optional[str], name: str,
             local_types: Dict[str, str], import_simple: Dict[str, str],
             simple_to_owner: Dict[str, List[str]],
             method_owners: Dict[str, List[str]],
             graph: JavaCallGraph) -> Optional[str]:
    """Best guess at which declared method a call site reaches."""
    # 1. Unqualified, or through this: the same type.
    if receiver in (None, "this", "super"):
        candidate = f"{caller_owner}#{name}"
        if candidate in graph.methods:
            return candidate

    # 2. Through a field or local whose declared type we know.
    if receiver and receiver in local_types:
        owner = _owner_for(local_types[receiver], import_simple, simple_to_owner)
        if owner:
            candidate = f"{owner}#{name}"
            if candidate in graph.methods:
                return candidate

    # 3. A static call through a type name.
    if receiver and receiver[:1].isupper():
        owner = _owner_for(receiver, import_simple, simple_to_owner)
        if owner:
            candidate = f"{owner}#{name}"
            if candidate in graph.methods:
                return candidate

    # 4. A method name declared by exactly one type in the repository.
    owners = set(method_owners.get(name, []))
    if len(owners) == 1:
        candidate = f"{next(iter(owners))}#{name}"
        if candidate in graph.methods:
            return candidate
    return None


def methods_for_lines(graph: JavaCallGraph, path: str,
                      lines: Iterable[int]) -> List[str]:
    """Which methods a set of changed line numbers falls inside."""
    wanted = set(lines)
    out = []
    for decl in graph.methods_in_file(path):
        if any(decl.contains(line) for line in wanted):
            out.append(decl.key)
    return sorted(out)
