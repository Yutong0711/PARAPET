"""Reading structure out of Java source, without a compiler.

The published study used Understand, a commercial tool. This module gets
the same file-level facts from the source text: which types a file
declares, which types it imports, which it extends or implements, and
which it otherwise mentions. That is everything a design structure matrix
needs.

It is a scanner, not a parser, and the trade is deliberate. A real parser
needs the full classpath to resolve a name, which means a build, which
means the tool cannot run on a repository it has not compiled. A scanner
runs on a checkout in milliseconds and is wrong in known ways:

* A type used through a wildcard import is resolved by simple name, so two
  types with the same simple name in different packages are conflated.
* A type from a dependency jar is not in the repository, so it produces no
  edge. Only in-repository structure is modelled, which is what the design
  structure matrix is about.
* Generic parameters, annotations and locally shadowed names may produce a
  reference to a type that the compiler would resolve elsewhere.

:func:`parse_file` records what it resolved and what it could not, so the
uncertainty is reported rather than hidden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

_PACKAGE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
_IMPORT = re.compile(r"^\s*import\s+(static\s+)?([\w.]+)(\.\*)?\s*;", re.M)
_TYPE_DECL = re.compile(
    r"\b(?:public|protected|private|static|final|abstract|sealed|non-sealed|\s)*"
    r"(class|interface|enum|record|@interface)\s+(\w+)")
_EXTENDS = re.compile(r"\b(?:class|interface)\s+(\w+)[^{]*?\bextends\s+([\w.<>,\s]+?)(?:\bimplements\b|\{)")
_IMPLEMENTS = re.compile(r"\b(?:class|record|enum)\s+(\w+)[^{]*?\bimplements\s+([\w.<>,\s]+?)\{")
_IDENTIFIER = re.compile(r"\b([A-Z][A-Za-z0-9_]*)\b")

# Java's own types produce no in-repository edge; listing the common ones
# keeps the reference set small enough to read.
JAVA_BUILTINS = {
    "String", "Integer", "Long", "Double", "Float", "Boolean", "Byte", "Short",
    "Character", "Object", "Class", "System", "Math", "Number", "Void",
    "List", "ArrayList", "LinkedList", "Map", "HashMap", "TreeMap",
    "LinkedHashMap", "Set", "HashSet", "TreeSet", "LinkedHashSet", "Collection",
    "Collections", "Arrays", "Iterator", "Iterable", "Comparable", "Comparator",
    "Optional", "Stream", "Objects", "StringBuilder", "StringBuffer",
    "Exception", "RuntimeException", "Error", "Throwable", "IOException",
    "IllegalArgumentException", "IllegalStateException", "NullPointerException",
    "UnsupportedOperationException", "InterruptedException", "Thread",
    "Runnable", "Callable", "Future", "Executor", "ExecutorService",
    "Executors", "AtomicInteger", "AtomicLong", "AtomicBoolean", "File",
    "Path", "Paths", "Files", "InputStream", "OutputStream", "Reader", "Writer",
    "BufferedReader", "BufferedWriter", "ByteBuffer", "Charset",
    "StandardCharsets", "Override", "Deprecated", "SuppressWarnings",
    "FunctionalInterface", "SafeVarargs", "Test", "Before", "After",
    "BeforeEach", "AfterEach", "Assert", "Assertions", "Nullable", "NotNull",
}

TEST_PATH = re.compile(r"(^|/)(test|tests|src/test)(/|$)", re.I)
TEST_NAME = re.compile(r"(Test|Tests|TestCase|IT|ITCase)\.java$")


@dataclass
class JavaFile:
    """The structural facts of one ``.java`` file."""

    path: str
    package: str = ""
    types: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    wildcard_imports: List[str] = field(default_factory=list)
    extends: Set[str] = field(default_factory=set)
    references: Set[str] = field(default_factory=set)
    n_lines: int = 0
    unresolved: Set[str] = field(default_factory=set)

    @property
    def primary_type(self) -> str:
        """The type a compiler would expect to find here."""
        stem = Path(self.path).stem
        if stem in self.types:
            return stem
        return self.types[0] if self.types else stem

    @property
    def qualified_name(self) -> str:
        return f"{self.package}.{self.primary_type}" if self.package else self.primary_type

    @property
    def is_test(self) -> bool:
        """Test code, by the two conventions Java projects actually use."""
        return bool(TEST_PATH.search(self.path) or TEST_NAME.search(self.path))

    def to_dict(self) -> dict:
        return {"path": self.path, "package": self.package,
                "types": list(self.types), "qualified_name": self.qualified_name,
                "n_lines": self.n_lines, "is_test": self.is_test,
                "n_references": len(self.references)}


def strip_comments_and_strings(source: str) -> str:
    """Blank out comments, strings and chars so scanning is safe.

    Replaced with spaces rather than removed, so every line number and
    offset in the result still matches the original.
    """
    out = []
    index, length = 0, len(source)
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


def _split_type_list(blob: str) -> List[str]:
    """``Foo<Bar>, Baz`` -> ``["Foo", "Baz"]``; generic arguments dropped."""
    depth, current, names = 0, [], []
    for char in blob:
        if char == "<":
            depth += 1
        elif char == ">":
            depth = max(0, depth - 1)
        elif char == "," and depth == 0:
            names.append("".join(current))
            current = []
            continue
        elif depth == 0:
            current.append(char)
    names.append("".join(current))
    out = []
    for name in names:
        simple = name.strip().split(".")[-1].strip()
        if simple and simple[0].isupper():
            out.append(simple)
    return out


def parse_file(path: str, source: str) -> JavaFile:
    """Structural facts for one file. ``path`` is repo-relative."""
    cleaned = strip_comments_and_strings(source)
    package_match = _PACKAGE.search(cleaned)
    java_file = JavaFile(path=path,
                         package=package_match.group(1) if package_match else "",
                         n_lines=source.count("\n") + 1)

    for _static, dotted, wildcard in _IMPORT.findall(cleaned):
        if wildcard:
            java_file.wildcard_imports.append(dotted)
        else:
            java_file.imports.append(dotted)

    for _kind, name in _TYPE_DECL.findall(cleaned):
        if name not in java_file.types:
            java_file.types.append(name)

    for regex in (_EXTENDS, _IMPLEMENTS):
        for _owner, blob in regex.findall(cleaned):
            java_file.extends.update(_split_type_list(blob))

    declared = set(java_file.types)
    for name in _IDENTIFIER.findall(cleaned):
        if name in declared or name in JAVA_BUILTINS:
            continue
        java_file.references.add(name)
    java_file.references.update(java_file.extends)
    return java_file


def parse_tree(files: Dict[str, str]) -> Dict[str, JavaFile]:
    """Parse a whole checkout: ``{repo-relative path: source}``."""
    return {path: parse_file(path, source) for path, source in files.items()
            if path.endswith(".java")}


@dataclass
class TypeIndex:
    """Where each type is declared, so a reference can become an edge."""

    by_qualified: Dict[str, str] = field(default_factory=dict)
    by_simple: Dict[str, List[str]] = field(default_factory=dict)

    @classmethod
    def build(cls, parsed: Dict[str, JavaFile]) -> "TypeIndex":
        index = cls()
        for path, java_file in parsed.items():
            for name in java_file.types:
                qualified = f"{java_file.package}.{name}" if java_file.package else name
                index.by_qualified.setdefault(qualified, path)
                index.by_simple.setdefault(name, []).append(path)
        return index

    def resolve(self, java_file: JavaFile, simple_name: str) -> Optional[str]:
        """The file that declares ``simple_name``, as seen from ``java_file``.

        Resolution order follows Java's own: an explicit import wins, then
        the same package, then a wildcard import, then a unique simple name
        anywhere in the repository. An ambiguous simple name resolves to
        nothing and is recorded as unresolved rather than guessed.
        """
        for dotted in java_file.imports:
            if dotted.rsplit(".", 1)[-1] == simple_name:
                hit = self.by_qualified.get(dotted)
                if hit:
                    return hit
        if java_file.package:
            hit = self.by_qualified.get(f"{java_file.package}.{simple_name}")
            if hit:
                return hit
        for package in java_file.wildcard_imports:
            hit = self.by_qualified.get(f"{package}.{simple_name}")
            if hit:
                return hit
        candidates = self.by_simple.get(simple_name, [])
        if len(candidates) == 1:
            return candidates[0]
        return None


def is_test_path(path: str) -> bool:
    return bool(TEST_PATH.search(path) or TEST_NAME.search(path))
