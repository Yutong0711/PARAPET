"""parapet-scope: how wide is this change, and how should it be reviewed.

A diffstat says how many lines moved. It does not say whether the change
re-pointed four files onto a new one, or repeated the same edit across
seven siblings, or quietly widened an interface. Those are the facts that
decide how long a review takes and where it should start, and they live in
the structure between files, not in the diff.

    from parapet_scope import analyse, build_diff_dsm, load_revision

    revision = load_revision("path/to/repo", "HEAD")
    diff = build_diff_dsm(revision.before, revision.after, revision.changed,
                          change_ref=revision.short)
    verdict = analyse(diff, revision.before, revision.after)
    print(verdict.advice())

Java only, for now. The structural facts come from a source scanner rather
than a compiler, so the tool runs on a checkout without a build; see
:mod:`parapet_scope.javasrc` for what that costs.
"""

from .classify import (COCHANGE_PATTERNS, DESIGN_LEVEL, LOCALIZED, ScopeVerdict,
                       analyse, classify_scope, detect_cochange,
                       detect_design_pattern, review_order)
from .dsm import DEPENDS, DSM, EXTENDS, DiffDSM, build_diff_dsm, build_dsm
from .gitsource import GitError, Revision, changed_files, load_revision
from .javasrc import JavaFile, TypeIndex, is_test_path, parse_file, parse_tree

__all__ = [
    "analyse", "classify_scope", "detect_design_pattern", "detect_cochange",
    "review_order", "ScopeVerdict", "LOCALIZED", "DESIGN_LEVEL",
    "COCHANGE_PATTERNS",
    "DSM", "DiffDSM", "build_dsm", "build_diff_dsm", "EXTENDS", "DEPENDS",
    "load_revision", "changed_files", "Revision", "GitError",
    "JavaFile", "TypeIndex", "parse_file", "parse_tree", "is_test_path",
]
__version__ = "0.1.0"
