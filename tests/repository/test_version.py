"""Repository sanity checks for PARAPET's own version identifier.

STRUCTURAL, NOT FUNCTIONAL.

``VERSION`` is the single source of truth for the PARAPET release version.
Human-facing text says "v1.0". These checks keep the two in step and make sure
the repository never claims that a Git tag or GitHub Release already exists.

Upstream version strings inside ``projects/`` (the Derui Zhu artifact bundle
v1.0, PEFT 0.3.0.dev0, MIMIR 1.0, and so on) belong to third parties and are
deliberately out of scope here.
"""

from __future__ import annotations

import re

import pytest

# PARAPET-owned files that carry human-facing version text.
PARAPET_OWNED_TEXT = ("README.md", "CHANGELOG.md", "CONTRIBUTING.md")


@pytest.fixture(scope="module")
def version(repo_root):
    return (repo_root / "VERSION").read_text(encoding="utf-8").strip()


class TestVersionFile:
    def test_version_file_exists_and_holds_a_bare_version(self, repo_root):
        raw = (repo_root / "VERSION").read_text(encoding="utf-8")

        assert raw == "1.0\n", "VERSION must contain exactly '1.0' and a trailing newline"

    def test_version_matches_a_simple_numeric_form(self, version):
        assert re.fullmatch(r"\d+\.\d+", version)


class TestReadmeAgreesWithVersionFile:
    def test_readme_advertises_the_same_version(self, repo_root, version):
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        # Must name PARAPET's own version explicitly. A bare "v1.0" is not
        # enough: the projects table also cites the third-party
        # "Derui Zhu artifact bundle v1.0".
        assert f"PARAPET v{version}" in readme

    def test_changelog_has_a_section_for_this_version(self, repo_root, version):
        changelog = repo_root / "CHANGELOG.md"
        if not changelog.is_file():
            pytest.skip("CHANGELOG.md is not present")

        assert re.search(rf"^##\s*\[?v?{re.escape(version)}\]?", changelog.read_text(encoding="utf-8"), re.M)


class TestNoStalePrereleaseVersion:
    @pytest.mark.parametrize("doc", PARAPET_OWNED_TEXT)
    def test_no_parapet_owned_doc_still_says_0_1(self, repo_root, doc):
        path = repo_root / doc
        if not path.is_file():
            pytest.skip(f"{doc} is not present")

        text = path.read_text(encoding="utf-8")
        stale = re.findall(r"PARAPET[^\n]{0,40}\bv?0\.1(?:\.0)?\b", text)

        assert stale == [], f"{doc} still refers to a pre-1.0 PARAPET version: {stale}"

    def test_the_website_does_not_advertise_a_stale_parapet_version(self, repo_root):
        html = (repo_root / "index.html").read_text(encoding="utf-8")

        assert not re.search(r"PARAPET[^<]{0,40}\bv?0\.1(?:\.0)?\b", html)


class TestNoPrematureReleaseClaims:
    @pytest.mark.parametrize("doc", PARAPET_OWNED_TEXT)
    def test_no_doc_claims_the_tag_or_release_already_exists(self, repo_root, doc):
        """The v1.0 tag and GitHub Release are created manually after review."""
        path = repo_root / doc
        if not path.is_file():
            pytest.skip(f"{doc} is not present")

        text = path.read_text(encoding="utf-8").lower()
        forbidden = [
            "has been tagged",
            "has been released",
            "was released on",
            "download the v1.0 release",
        ]

        found = [phrase for phrase in forbidden if phrase in text]
        assert found == [], f"{doc} claims a release that does not exist yet: {found}"
