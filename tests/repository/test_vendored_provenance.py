"""Repository sanity checks for vendored artifact provenance.

STRUCTURAL, NOT FUNCTIONAL. These checks assert that the six vendored research
snapshots are still present and still carry the provenance banners that say
where they came from. They say nothing about whether the vendored code works.

They exist because PARAPET redistributes other people's research artifacts:
losing a provenance banner or a source directory in a refactor is a real
attribution failure, and it is cheap to catch automatically.
"""

from __future__ import annotations

import pytest

# name -> (upstream origin keyword expected in the provenance banner)
VENDORED_PROJECTS = {
    "perforch": "github.com/qzydustin/perforch",
    "coquir": "Derui Zhu Prior Research Code Artifacts",
    "metior": "ASE 2021 research artifact",
    "luna": "Derui Zhu Prior Research Code Artifacts",
    "privauditor": "Derui Zhu Prior Research Code Artifacts",
    "more-than-just-functional": "Derui Zhu Prior Research Code Artifacts",
}


@pytest.mark.parametrize("project", sorted(VENDORED_PROJECTS))
def test_vendored_project_directory_exists(projects_dir, project):
    assert (projects_dir / project).is_dir()


@pytest.mark.parametrize("project", sorted(VENDORED_PROJECTS))
def test_vendored_project_has_a_readme(projects_dir, project):
    assert (projects_dir / project / "README.md").is_file()


@pytest.mark.parametrize("project", sorted(VENDORED_PROJECTS))
def test_vendored_project_has_a_source_tree(projects_dir, project):
    src = projects_dir / project / "src"

    assert src.is_dir()
    assert any(src.rglob("*.py")), f"{project}/src contains no Python sources"


@pytest.mark.parametrize(("project", "origin"), sorted(VENDORED_PROJECTS.items()))
def test_readme_opens_with_a_vendored_snapshot_banner(projects_dir, project, origin):
    readme = (projects_dir / project / "README.md").read_text(encoding="utf-8")
    head = "\n".join(readme.splitlines()[:8])

    assert "Vendored snapshot" in head, f"{project}/README.md lost its provenance banner"
    assert origin in head, f"{project}/README.md no longer names its upstream origin"


def test_no_undeclared_project_directory_appears(projects_dir):
    """A new folder under projects/ must be declared here with its provenance."""
    found = {p.name for p in projects_dir.iterdir() if p.is_dir()}

    assert found == set(VENDORED_PROJECTS)


@pytest.mark.parametrize(
    "project", ["coquir", "luna", "more-than-just-functional", "privauditor"]
)
def test_pesose_role_note_is_preserved(projects_dir, project):
    """The PESOSE-authored scope notes explain why each artifact is included."""
    role = projects_dir / project / "PESOSE_ROLE.md"

    assert role.is_file()
    assert "PESOSE role" in role.read_text(encoding="utf-8")


def test_the_perforch_snapshot_records_its_parapet_maintained_change(projects_dir):
    """PerfOrch is the one snapshot PARAPET modified; that must not go silent.

    The vendored runtime built its command as a shell string, so a checkout or
    interpreter path containing a space was torn into two arguments and the
    Python backend could not run. PARAPET fixed it here. Redistributing a
    modified artifact without saying so is an attribution failure, so the
    banner has to keep saying it.
    """
    readme = (projects_dir / "perforch" / "README.md").read_text(encoding="utf-8")

    assert "PARAPET-maintained change" in readme, (
        "projects/perforch/README.md no longer discloses that this snapshot "
        "differs from upstream"
    )
    assert "src/runtime_processors/core.py" in readme
    assert "src/runtime_processors/python_processor.py" in readme


def test_the_perforch_banner_does_not_claim_upstream_carries_the_fix(projects_dir):
    """The fix is not at the pinned commit and upstream was not re-checked."""
    readme = (projects_dir / "perforch" / "README.md").read_text(encoding="utf-8")
    banner = readme.split("PARAPET-maintained change", 1)[1].split("\n\n", 1)[0]

    assert "not** present at the pinned commit" in banner or "not present at the pinned commit" in banner
    assert "has not been" in banner and "verified" in banner


def test_every_vendored_python_source_parses(projects_dir):
    """A truncated or corrupted vendored file is silent data loss.

    Parsing (rather than importing) needs no third-party dependencies, so this
    covers all six snapshots including the ones whose runtime requirements --
    torch, mteb, transformers, GPUs -- are unavailable in CI.
    """
    import ast
    import warnings

    unparsable = []
    sources = sorted(projects_dir.rglob("*.py"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for source in sources:
            try:
                ast.parse(source.read_text(encoding="utf-8", errors="strict"))
            except (SyntaxError, UnicodeDecodeError) as exc:
                unparsable.append(f"{source.relative_to(projects_dir)}: {exc}")

    assert len(sources) > 100, "expected the vendored snapshots to contain many Python sources"
    assert unparsable == []
