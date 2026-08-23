"""Reading two checkouts out of a git repository.

Everything ``parapet-scope`` needs from git is here: the files a commit
changed, and the content of the tree before and after it. Nothing else
shells out, so a caller with sources already in hand can use
:mod:`parapet_scope.dsm` directly and skip git entirely.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


class GitError(RuntimeError):
    """A git command failed, with the command and stderr kept."""


def _git(repo: Path, *args: str, timeout: int = 120) -> str:
    try:
        result = subprocess.run(["git", "-C", str(repo), *args],
                                capture_output=True, text=True, check=False,
                                timeout=timeout)
    except FileNotFoundError as exc:
        raise GitError("git is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git {' '.join(args)} timed out") from exc
    if result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def resolve(repo: Path, rev: str) -> str:
    """Turn a revision expression into a commit hash."""
    return _git(repo, "rev-parse", rev).strip()


def parent_of(repo: Path, commit: str) -> Optional[str]:
    """The first parent, or ``None`` for a root commit."""
    parents = _git(repo, "rev-list", "--parents", "-n", "1", commit).split()
    return parents[1] if len(parents) > 1 else None


def changed_files(repo: Path, commit: str, base: Optional[str] = None,
                  suffix: str = ".java") -> List[str]:
    """Files a commit touched, filtered by suffix.

    A root commit has nothing to diff against, so its whole tree counts as
    added.
    """
    base = base or parent_of(repo, commit)
    if base is None:
        output = _git(repo, "ls-tree", "-r", "--name-only", commit)
    else:
        output = _git(repo, "diff", "--name-only", f"{base}..{commit}")
    return [line.strip() for line in output.splitlines()
            if line.strip() and (not suffix or line.strip().endswith(suffix))]


def list_tree(repo: Path, commit: str, suffix: str = ".java",
              paths: Optional[Sequence[str]] = None) -> List[str]:
    args = ["ls-tree", "-r", "--name-only", commit]
    if paths:
        args += ["--", *paths]
    return [line.strip() for line in _git(repo, *args).splitlines()
            if line.strip() and (not suffix or line.strip().endswith(suffix))]


def read_tree(repo: Path, commit: str, paths: Sequence[str]) -> Dict[str, str]:
    """Read the content of specific paths at one commit.

    A path missing at that commit is skipped rather than raising: a file
    added by the revision does not exist in the parent, and that absence is
    exactly what makes it an added file.
    """
    sources: Dict[str, str] = {}
    for path in paths:
        try:
            sources[path] = _git(repo, "show", f"{commit}:{path}")
        except GitError:
            continue
    return sources


@dataclass
class Revision:
    """One revision, with the two trees a Diff-DSM needs."""

    repo: Path
    commit: str
    base: str
    changed: List[str]
    before: Dict[str, str]
    after: Dict[str, str]
    subject: str = ""

    @property
    def short(self) -> str:
        return self.commit[:12]


def load_revision(repo: Path, commit: str = "HEAD",
                  base: Optional[str] = None,
                  scope: str = "neighbourhood",
                  suffix: str = ".java") -> Revision:
    """Load the trees needed to diff one revision.

    ``scope`` decides how much of the repository is read:

    ``changed``
        only the files the revision touched. Fastest, but a reference from
        an unchanged file cannot be resolved, so propagation is invisible.
    ``neighbourhood``
        the changed files plus every file in the same directories. A good
        default: it resolves most in-package references at a fraction of
        the cost of the whole tree.
    ``full``
        the whole tree at both commits. Most accurate, slowest, and the
        only choice that resolves a reference from anywhere in the system.
    """
    repo = Path(repo)
    commit = resolve(repo, commit)
    base = resolve(repo, base) if base else (parent_of(repo, commit) or commit)
    changed = changed_files(repo, commit, base, suffix)

    if scope == "changed":
        wanted_after = list(changed)
        wanted_before = list(changed)
    elif scope == "full":
        wanted_after = list_tree(repo, commit, suffix)
        wanted_before = list_tree(repo, base, suffix)
    elif scope == "neighbourhood":
        directories = sorted({str(Path(path).parent) for path in changed} or {"."})
        wanted_after = sorted(set(list_tree(repo, commit, suffix, directories))
                              | set(changed))
        wanted_before = sorted(set(list_tree(repo, base, suffix, directories))
                               | set(changed))
    else:
        raise ValueError(f"unknown scope {scope!r}; expected 'changed', "
                         "'neighbourhood' or 'full'")

    subject = _git(repo, "log", "-1", "--format=%s", commit).strip()
    return Revision(repo=repo, commit=commit, base=base, changed=changed,
                    before=read_tree(repo, base, wanted_before),
                    after=read_tree(repo, commit, wanted_after),
                    subject=subject)


def issue_keys(repo: Path, commit: str) -> List[str]:
    """Issue keys named in the commit message, e.g. ``AVRO-753``."""
    import re
    message = _git(repo, "log", "-1", "--format=%B", commit)
    seen, out = set(), []
    for key in re.findall(r"\b([A-Z][A-Z0-9]{1,15}-\d+)\b", message):
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out
