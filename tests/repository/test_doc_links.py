"""Repository sanity checks for internal documentation links.

STRUCTURAL, NOT FUNCTIONAL.

Only PARAPET-authored documents are checked: the root docs and the
``PESOSE_ROLE.md`` scope notes. Vendored upstream README bodies are deliberately
excluded -- their links point into upstream trees that were not vendored, and
rewriting them would damage provenance. The one exception is the provenance
banner PARAPET prepends to each vendored README, which is PARAPET-authored and
is checked.
"""

from __future__ import annotations

import re

import pytest

PARAPET_OWNED_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
]

PESOSE_ROLE_NOTES = [
    "projects/coquir/PESOSE_ROLE.md",
    "projects/luna/PESOSE_ROLE.md",
    "projects/more-than-just-functional/PESOSE_ROLE.md",
    "projects/privauditor/PESOSE_ROLE.md",
]

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
BACKTICK_PATH = re.compile(r"`(projects/[A-Za-z0-9_./-]+)`")


def _local_link_targets(text):
    """Yield link targets that point at files in this repository."""
    for target in MARKDOWN_LINK.findall(text):
        target = target.split("#", 1)[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        yield target


@pytest.mark.parametrize("doc", PARAPET_OWNED_DOCS)
def test_root_document_links_resolve(repo_root, doc):
    path = repo_root / doc
    if not path.is_file():
        pytest.skip(f"{doc} is not present")

    broken = [
        target
        for target in _local_link_targets(path.read_text(encoding="utf-8"))
        if not (repo_root / target).exists()
    ]

    assert broken == [], f"{doc} links to missing paths: {broken}"


@pytest.mark.parametrize("doc", PARAPET_OWNED_DOCS)
def test_root_document_backticked_project_paths_resolve(repo_root, doc):
    path = repo_root / doc
    if not path.is_file():
        pytest.skip(f"{doc} is not present")

    text = path.read_text(encoding="utf-8")
    missing = [p for p in BACKTICK_PATH.findall(text) if not (repo_root / p.rstrip("/")).exists()]

    assert missing == [], f"{doc} cites missing project paths: {missing}"


@pytest.mark.parametrize("note", PESOSE_ROLE_NOTES)
def test_pesose_role_note_links_resolve(repo_root, note):
    path = repo_root / note
    base = path.parent

    broken = [
        target
        for target in _local_link_targets(path.read_text(encoding="utf-8"))
        if not (base / target).exists()
    ]

    assert broken == [], f"{note} links to missing paths: {broken}"


@pytest.mark.parametrize("note", PESOSE_ROLE_NOTES)
def test_pesose_role_note_backticked_paths_resolve(repo_root, note):
    """Catches references such as `../../docs/LICENSE_AND_PROVENANCE.md`."""
    path = repo_root / note
    base = path.parent
    text = path.read_text(encoding="utf-8")

    cited = re.findall(r"`(\.\.?/[A-Za-z0-9_./-]+)`", text)
    missing = [p for p in cited if not (base / p).exists()]

    assert missing == [], f"{note} cites missing paths: {missing}"


@pytest.mark.parametrize(
    "project",
    ["coquir", "luna", "metior", "more-than-just-functional", "perforch", "privauditor"],
)
def test_vendored_readme_provenance_banner_links_resolve(repo_root, projects_dir, project):
    """Only the PARAPET-authored banner at the top of each vendored README."""
    readme = projects_dir / project / "README.md"
    text = readme.read_text(encoding="utf-8")
    banner = "\n".join(line for line in text.splitlines()[:8] if line.startswith(">"))

    broken = [
        target
        for target in _local_link_targets(banner)
        if not (readme.parent / target).exists()
    ]

    assert broken == [], f"{project}/README.md provenance banner links to missing paths: {broken}"
