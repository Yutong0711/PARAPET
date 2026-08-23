"""Design structure matrices, and the difference one revision makes.

A DSM is a square matrix over the source files of a system. Cell
``[row, column]`` holds the structural dependencies of the file on the row
on the file on the column. Two dependency kinds are modelled: ``ext`` for
inheritance and ``dp`` for every other structural reference.

A Diff-DSM is the difference between the DSM before a revision and the DSM
after it, restricted to the files the revision touched. It marks files the
revision added or removed and dependencies it added or removed, which is
what makes a design-level change visible as a shape rather than as a
diffstat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

from .javasrc import JavaFile, TypeIndex, is_test_path, parse_tree

EXTENDS = "ext"
DEPENDS = "dp"

Edge = Tuple[str, str, str]     # (from path, to path, kind)


@dataclass(frozen=True)
class DSM:
    """Files and their structural dependencies at one revision."""

    files: Tuple[str, ...]
    edges: FrozenSet[Edge] = frozenset()
    unresolved: Tuple[Tuple[str, str], ...] = ()

    @classmethod
    def build(cls, files: Sequence[str], edges: Iterable[Edge] = (),
              unresolved: Iterable[Tuple[str, str]] = ()) -> "DSM":
        ordered = tuple(dict.fromkeys(files))
        allowed = set(ordered)
        cleaned = {edge for edge in edges
                   if edge[0] in allowed and edge[1] in allowed and edge[0] != edge[1]}
        return cls(ordered, frozenset(cleaned), tuple(unresolved))

    def dependencies_of(self, path: str) -> Set[Tuple[str, str]]:
        return {(target, kind) for source, target, kind in self.edges
                if source == path}

    def dependents_of(self, path: str) -> Set[Tuple[str, str]]:
        return {(source, kind) for source, target, kind in self.edges
                if target == path}

    def subset(self, paths: Iterable[str]) -> "DSM":
        keep = set(paths)
        return DSM.build([f for f in self.files if f in keep],
                         [e for e in self.edges if e[0] in keep and e[1] in keep])

    def render(self, max_files: int = 20) -> str:
        """The tabular view, small enough to read in a terminal."""
        shown = list(self.files[:max_files])
        index = {path: position + 1 for position, path in enumerate(shown)}
        labels = [_short(path) for path in shown]
        width = max((len(label) for label in labels), default=8) + 2
        lines = [" " * (width + 5) + "".join(f"{i:>5}" for i in index.values())]
        for path, label in zip(shown, labels):
            cells = []
            for other in shown:
                if other == path:
                    cells.append(f"({index[path]})".rjust(5))
                    continue
                kinds = sorted(kind for target, kind in self.dependencies_of(path)
                               if target == other)
                cells.append(("/".join(kinds) if kinds else "").rjust(5))
            lines.append(f"{index[path]:>3}  {label:<{width}}" + "".join(cells))
        if len(self.files) > max_files:
            lines.append(f"     ... {len(self.files) - max_files} more file(s)")
        return "\n".join(lines)

    def summary(self) -> dict:
        return {"n_files": len(self.files), "n_edges": len(self.edges),
                "n_unresolved": len(self.unresolved)}


def _short(path: str) -> str:
    stem = path.rsplit("/", 1)[-1]
    return stem[:-5] if stem.endswith(".java") else stem


def build_dsm(sources: Dict[str, str],
              restrict_to: Optional[Iterable[str]] = None) -> DSM:
    """Build a DSM from ``{repo-relative path: source}``.

    ``restrict_to`` keeps only those files and the edges among them, which
    is how a Diff-DSM narrows the picture to the revision's neighbourhood.
    """
    parsed = parse_tree(sources)
    index = TypeIndex.build(parsed)
    edges: Set[Edge] = set()
    unresolved: List[Tuple[str, str]] = []

    for path, java_file in parsed.items():
        for name in sorted(java_file.references):
            target = index.resolve(java_file, name)
            if target is None:
                unresolved.append((path, name))
                continue
            if target == path:
                continue
            kind = EXTENDS if name in java_file.extends else DEPENDS
            edges.add((path, target, kind))

    dsm = DSM.build(sorted(parsed), edges, unresolved)
    if restrict_to is not None:
        dsm = dsm.subset(restrict_to)
    return dsm


@dataclass
class DiffDSM:
    """What one revision did to the design structure."""

    before: DSM
    after: DSM
    changed_files: Tuple[str, ...] = ()
    change_ref: str = ""
    notes: Dict[str, str] = field(default_factory=dict)

    @property
    def added_files(self) -> Tuple[str, ...]:
        return tuple(f for f in self.after.files if f not in set(self.before.files))

    @property
    def removed_files(self) -> Tuple[str, ...]:
        return tuple(f for f in self.before.files if f not in set(self.after.files))

    @property
    def added_edges(self) -> Tuple[Edge, ...]:
        return tuple(sorted(self.after.edges - self.before.edges))

    @property
    def removed_edges(self) -> Tuple[Edge, ...]:
        return tuple(sorted(self.before.edges - self.after.edges))

    @property
    def production_files(self) -> Tuple[str, ...]:
        return tuple(f for f in self.changed_files if not is_test_path(f))

    @property
    def test_files(self) -> Tuple[str, ...]:
        return tuple(f for f in self.changed_files if is_test_path(f))

    @property
    def touched(self) -> Tuple[str, ...]:
        """Every file the revision edited, added, removed or re-wired."""
        seen = set(self.changed_files) | set(self.added_files) | set(self.removed_files)
        for source, target, _kind in self.added_edges + self.removed_edges:
            seen.add(source)
            seen.add(target)
        order = list(self.after.files) + [f for f in self.before.files
                                          if f not in set(self.after.files)]
        return tuple(f for f in order if f in seen)

    @property
    def structure_changed(self) -> bool:
        return bool(self.added_files or self.removed_files
                    or self.added_edges or self.removed_edges)

    def render(self, max_files: int = 20) -> str:
        lines = [f"Diff-DSM {self.change_ref or '(unnamed revision)'}",
                 f"  production files changed: {len(self.production_files)}",
                 f"  test files changed:       {len(self.test_files)}",
                 f"  files added:   {[_short(f) for f in self.added_files] or 'none'}",
                 f"  files removed: {[_short(f) for f in self.removed_files] or 'none'}",
                 f"  dependencies added:   {len(self.added_edges)}",
                 f"  dependencies removed: {len(self.removed_edges)}"]
        for source, target, kind in self.added_edges[:12]:
            lines.append(f"    + {_short(source)} -> {_short(target)} ({kind})")
        for source, target, kind in self.removed_edges[:12]:
            lines.append(f"    - {_short(source)} -> {_short(target)} ({kind})")
        if self.touched:
            lines.append("")
            lines.append(self.after.subset(self.touched).render(max_files))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "change_ref": self.change_ref,
            "changed_files": list(self.changed_files),
            "production_files": list(self.production_files),
            "test_files": list(self.test_files),
            "added_files": list(self.added_files),
            "removed_files": list(self.removed_files),
            "added_dependencies": [list(edge) for edge in self.added_edges],
            "removed_dependencies": [list(edge) for edge in self.removed_edges],
            "before": self.before.summary(),
            "after": self.after.summary(),
        }


def build_diff_dsm(before_sources: Dict[str, str],
                   after_sources: Dict[str, str],
                   changed_files: Sequence[str],
                   change_ref: str = "",
                   neighbourhood: int = 1) -> DiffDSM:
    """Diff two checkouts, keeping the changed files and their neighbours.

    ``neighbourhood`` is how far to reach around the changed files. Zero
    keeps only the changed files, which hides the propagation that makes a
    change design-level; one keeps their direct dependents and
    dependencies, which is the picture the published figures draw.
    """
    full_before = build_dsm(before_sources)
    full_after = build_dsm(after_sources)

    keep = set(changed_files)
    for _ in range(max(0, neighbourhood)):
        grown = set(keep)
        for dsm in (full_before, full_after):
            for source, target, _kind in dsm.edges:
                if source in keep:
                    grown.add(target)
                if target in keep:
                    grown.add(source)
        keep = grown

    return DiffDSM(before=full_before.subset(keep),
                   after=full_after.subset(keep),
                   changed_files=tuple(changed_files),
                   change_ref=change_ref)
