"""What a change costs a human to review.

Two questions, answered from the Diff-DSM:

**How wide is it?** A *localized* change is a few lines in a single file.
A *design-level* change is a coordinated revision of a group of files and
the structure between them. The distinction is not the file count: a
change touching six files that adds no dependency and removes none is six
localized changes in one commit, while a change touching two files that
adds a new one and re-points four dependents onto it is design-level.

**What shape is it?** Four shapes recur, and each tells a reviewer where
to look:

``Change Propagation (Type-I)``
    a new file carries the change and existing files adopt it. Review the
    new file first, then check that every adopter really needed to move.
``Change Propagation (Type-II)``
    dependencies are re-pointed among existing files, with nothing new.
    Review the re-pointing: this is where a change quietly widens an API.
``Optimization Clone``
    the same edit repeated across siblings. Review one, then diff the rest
    against it; a clone that drifted is the bug.
``Parallel Optimization``
    several independent edits landing together. Review them separately;
    they only share a commit.

And the test side: which of the five test/production co-change patterns
the revision shows, which says whether the tests check the change or
merely still pass.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .dsm import DEPENDS, EXTENDS, DiffDSM
from .javasrc import is_test_path

LOCALIZED = "localized"
DESIGN_LEVEL = "design-level"

# A change confined to this many production files, with no structural
# change, is localized however many lines it moved.
LOCALIZED_MAX_FILES = 1
# Type-I needs a new file that this many existing files adopt. One adopter
# is a rename; two or more is propagation.
MIN_ADOPTERS = 2
# A clone needs this many siblings receiving the same edit.
MIN_CLONES = 3

COCHANGE_PATTERNS = ("Method Replacement", "Performance Input Revision",
                     "Test Logic Modification", "Test Case Addition",
                     "Test File Addition")


@dataclass
class ScopeVerdict:
    """The review-cost verdict for one revision."""

    change_ref: str
    scope: str
    design_pattern: Optional[str] = None
    pattern_reason: str = ""
    n_production_files: int = 0
    n_test_files: int = 0
    added_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    added_dependencies: int = 0
    removed_dependencies: int = 0
    cochange_patterns: List[str] = field(default_factory=list)
    review_order: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def is_design_level(self) -> bool:
        return self.scope == DESIGN_LEVEL

    def advice(self) -> str:
        """One paragraph telling a reviewer where to start."""
        if not self.is_design_level:
            return (f"{self.change_ref}: localized. "
                    f"{self.n_production_files} production file(s), no change "
                    "to the structure between files. Review the diff.")
        lines = [f"{self.change_ref}: design-level"
                 + (f", {self.design_pattern}." if self.design_pattern else ".")]
        if self.pattern_reason:
            lines.append(f"  why: {self.pattern_reason}")
        lines.append(f"  {self.n_production_files} production file(s), "
                     f"{self.added_dependencies} dependency(ies) added, "
                     f"{self.removed_dependencies} removed.")
        if self.review_order:
            lines.append("  review in this order: "
                         + " -> ".join(_short(p) for p in self.review_order[:6]))
        if self.cochange_patterns:
            lines.append(f"  tests: {', '.join(self.cochange_patterns)}")
        elif self.n_test_files == 0:
            lines.append("  tests: none changed. A design-level change with no "
                         "test revision is worth asking about.")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"change_ref": self.change_ref, "scope": self.scope,
                "design_pattern": self.design_pattern,
                "pattern_reason": self.pattern_reason,
                "n_production_files": self.n_production_files,
                "n_test_files": self.n_test_files,
                "added_files": list(self.added_files),
                "removed_files": list(self.removed_files),
                "added_dependencies": self.added_dependencies,
                "removed_dependencies": self.removed_dependencies,
                "cochange_patterns": list(self.cochange_patterns),
                "review_order": list(self.review_order),
                "notes": list(self.notes)}


def _short(path: str) -> str:
    stem = path.rsplit("/", 1)[-1]
    return stem[:-5] if stem.endswith(".java") else stem


def classify_scope(diff: DiffDSM) -> str:
    """Localized or design-level.

    Structure decides, not size. A change is design-level when it adds or
    removes a file, or adds or removes a dependency between files, or
    touches more than one production file in a way that the structure
    reflects.
    """
    production = [f for f in diff.production_files]
    if diff.added_files or diff.removed_files:
        return DESIGN_LEVEL
    if diff.added_edges or diff.removed_edges:
        return DESIGN_LEVEL
    if len(production) <= LOCALIZED_MAX_FILES:
        return LOCALIZED
    # Several production files, no structural change between them. That is
    # a group of localized edits, which is what the published coding calls
    # them, unless they are structurally connected to each other.
    connected = _connected_component(diff, production)
    return DESIGN_LEVEL if connected >= 2 and len(production) >= 3 else LOCALIZED


def _connected_component(diff: DiffDSM, files: Sequence[str]) -> int:
    """How many of the changed files depend on another changed file."""
    changed = set(files)
    linked = set()
    for source, target, _kind in diff.after.edges:
        if source in changed and target in changed:
            linked.add(source)
            linked.add(target)
    return len(linked)


def detect_design_pattern(diff: DiffDSM,
                          edit_signatures: Optional[Dict[str, str]] = None
                          ) -> Tuple[Optional[str], str]:
    """Name the design-level shape, and say what the evidence was."""
    added = set(diff.added_files)
    adopters = {source for source, target, _kind in diff.added_edges
                if target in added and source not in added}
    if added and len(adopters) >= MIN_ADOPTERS:
        return ("Change Propagation (Type-I)",
                f"{len(added)} new file(s) adopted by {len(adopters)} "
                "existing file(s)")

    rewired = [(source, target) for source, target, _kind
               in diff.added_edges + diff.removed_edges
               if source not in added and target not in added]
    if not added and rewired and len(diff.production_files) >= 2:
        return ("Change Propagation (Type-II)",
                f"{len(rewired)} dependency(ies) re-pointed among existing files")

    clones = _clone_group(diff, edit_signatures)
    if len(clones) >= MIN_CLONES:
        return ("Optimization Clone",
                f"the same edit in {len(clones)} file(s) sharing a supertype")

    if len(diff.production_files) >= 3 and not added and not rewired:
        return ("Parallel Optimization",
                f"{len(diff.production_files)} independent edits with no new "
                "dependency among them")

    if added:
        return (None, f"{len(added)} file(s) added but adopted by "
                      f"{len(adopters)} existing file(s); too few to call it "
                      "propagation")
    return (None, "no recognised shape")


def _clone_group(diff: DiffDSM,
                 edit_signatures: Optional[Dict[str, str]]) -> Set[str]:
    """Changed files that share a supertype and, if known, the same edit."""
    changed = set(diff.production_files)
    parents: Dict[str, Set[str]] = {}
    for source, target, kind in diff.after.edges:
        if kind == EXTENDS and source in changed:
            parents.setdefault(target, set()).add(source)
    siblings: Set[str] = set()
    for children in parents.values():
        if len(children) > len(siblings):
            siblings = children
    if not edit_signatures:
        return siblings
    grouped: Dict[str, Set[str]] = {}
    for path in siblings:
        signature = edit_signatures.get(path)
        if signature:
            grouped.setdefault(signature, set()).add(path)
    return max(grouped.values(), key=len, default=set())


def review_order(diff: DiffDSM) -> List[str]:
    """Where a reviewer should start, and what follows from it.

    New files first, because they carry the idea. Then the files that
    adopted them, then everything else the revision touched. A reviewer who
    reads in this order sees the change before its consequences.
    """
    added = list(diff.added_files)
    adopters = [source for source, target, _kind in diff.added_edges
                if target in set(added) and source not in set(added)]
    rest = [path for path in diff.production_files
            if path not in set(added) and path not in set(adopters)]
    ordered: List[str] = []
    for group in (added, sorted(set(adopters)), rest):
        for path in group:
            if path not in ordered:
                ordered.append(path)
    return ordered


# ---------------------------------------------------------------------------
# Test/production co-change
# ---------------------------------------------------------------------------

_METHOD_CALL = re.compile(r"\b(\w+)\s*\(")
_ASSERT = re.compile(r"\b(assert\w*|verify|expect|should\w*)\s*\(", re.I)
_TEST_ANNOTATION = re.compile(r"@(Test|ParameterizedTest|RepeatedTest)\b")
_LITERAL = re.compile(r'"[^"]*"|\b\d+(?:\.\d+)?[LlFfDd]?\b')


def detect_cochange(diff: DiffDSM,
                    before_sources: Dict[str, str],
                    after_sources: Dict[str, str]) -> List[str]:
    """Which of the five co-change patterns the revision shows.

    The distinction that matters is whether the tests were changed to check
    the new behaviour or merely to keep compiling. Only *Performance Input
    Revision* targets the change directly; the other four verify the
    functional logic around it.
    """
    tests = list(diff.test_files)
    if not tests:
        return []

    patterns: List[str] = []
    new_test_files = [path for path in diff.added_files if is_test_path(path)]
    if new_test_files:
        patterns.append("Test File Addition")

    for path in tests:
        if path in set(new_test_files):
            continue
        before = before_sources.get(path, "")
        after = after_sources.get(path, "")
        if not after:
            continue

        before_tests = len(_TEST_ANNOTATION.findall(before))
        after_tests = len(_TEST_ANNOTATION.findall(after))
        if after_tests > before_tests and "Test Case Addition" not in patterns:
            patterns.append("Test Case Addition")

        before_calls = set(_METHOD_CALL.findall(before))
        after_calls = set(_METHOD_CALL.findall(after))
        if (after_calls - before_calls) and (before_calls - after_calls) \
                and "Method Replacement" not in patterns:
            patterns.append("Method Replacement")

        before_literals = set(_LITERAL.findall(before))
        after_literals = set(_LITERAL.findall(after))
        literals_moved = before_literals != after_literals
        if literals_moved and before_calls == after_calls \
                and before_tests == after_tests \
                and "Performance Input Revision" not in patterns:
            patterns.append("Performance Input Revision")

        before_asserts = len(_ASSERT.findall(before))
        after_asserts = len(_ASSERT.findall(after))
        if before_asserts != after_asserts and after_tests == before_tests \
                and "Test Logic Modification" not in patterns:
            patterns.append("Test Logic Modification")

    if not patterns:
        patterns.append("Test Logic Modification")
    return patterns


def analyse(diff: DiffDSM,
            before_sources: Optional[Dict[str, str]] = None,
            after_sources: Optional[Dict[str, str]] = None,
            edit_signatures: Optional[Dict[str, str]] = None) -> ScopeVerdict:
    """The full review-cost verdict for one revision."""
    scope = classify_scope(diff)
    pattern, reason = (detect_design_pattern(diff, edit_signatures)
                       if scope == DESIGN_LEVEL else (None, ""))
    cochange = detect_cochange(diff, before_sources or {}, after_sources or {}) \
        if before_sources is not None else []

    verdict = ScopeVerdict(
        change_ref=diff.change_ref,
        scope=scope,
        design_pattern=pattern,
        pattern_reason=reason,
        n_production_files=len(diff.production_files),
        n_test_files=len(diff.test_files),
        added_files=list(diff.added_files),
        removed_files=list(diff.removed_files),
        added_dependencies=len(diff.added_edges),
        removed_dependencies=len(diff.removed_edges),
        cochange_patterns=cochange,
        review_order=review_order(diff) if scope == DESIGN_LEVEL else [])

    if diff.after.unresolved:
        verdict.notes.append(
            f"{len(diff.after.unresolved)} type reference(s) could not be "
            "resolved to a file in this repository; re-run with --scope full "
            "if the verdict looks wrong")
    if scope == DESIGN_LEVEL and not verdict.cochange_patterns \
            and verdict.n_test_files == 0:
        verdict.notes.append(
            "design-level change with no test revision")
    return verdict
