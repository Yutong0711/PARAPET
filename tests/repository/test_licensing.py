"""Repository sanity checks for the PARAPET v1.0 licensing boundary.

STRUCTURAL, NOT FUNCTIONAL.

PARAPET-owned repository content is Apache-2.0. The vendored artifacts under
``projects/`` keep their own licenses. Those two statements are easy to break
accidentally -- by overwriting a third-party LICENSE during a "licence
cleanup", or by leaving a stale MIT claim in the README -- and both mistakes
are legal problems rather than cosmetic ones, so they are checked.

Three of the vendored snapshots -- PerfOrch, LUNA, and More Than Just
Functional -- arrived without a license file. The project team, which owns or
controls those artifacts, has since released their *project-level* content
under Apache-2.0, and each directory now carries the canonical Apache-2.0 text.
That decision stops at the directory's own content: it does not reach any
third-party component nested inside, and the sharpest case is hmmlearn under
``projects/luna/``, which must stay BSD-3-Clause. Both halves are asserted
below -- the new licenses must be present and canonical, and the nested
BSD-3-Clause file must not have been swallowed by the LUNA one.

Every expectation below is derived from the license files actually checked in.
"""

from __future__ import annotations

import hashlib
import re

import pytest

# md5 of the canonical Apache License 2.0 text as published at
# https://www.apache.org/licenses/LICENSE-2.0.txt
CANONICAL_APACHE_2_MD5 = "3b83ef96387f14655fc854ddc3c6bd57"

# Project-level license files added under ``projects/`` by an explicit
# project-team licensing decision. Each must be the canonical Apache-2.0 text.
PROJECT_TEAM_APACHE_LICENSE_FILES = (
    "projects/perforch/LICENSE",
    "projects/luna/LICENSE",
    "projects/more-than-just-functional/LICENSE",
)

# Third-party license files that must survive intact, with a fingerprint taken
# from the file as vendored. These are NOT covered by the project-team decision
# above. Paths are relative to the repository root.
THIRD_PARTY_LICENSE_FILES = {
    "projects/coquir/LICENSE": "Apache License",
    "projects/metior/LICENSE.md": "BSD License 2.0",
    "projects/privauditor/LICENSE": "Apache License",
    "projects/privauditor/DATA_LICENSE": "Attribution License (ODC-By)",
    "projects/privauditor/src/peft/LICENSE": "Apache License",
    "projects/privauditor/src/mia-attack/mimir/LICENSE": "MIT License",
    "projects/luna/src/luna/hmmlearn/LICENSE.txt": "hmmlearn authors and contributors",
}

# PARAPET-owned files that describe the project's own license.
PARAPET_OWNED_DOCS = ("README.md", "CONTRIBUTING.md", "CHANGELOG.md", "THIRD_PARTY_NOTICES.md")

NON_APACHE_LICENSE = re.compile(r"\b(MIT|BSD|GPL|MPL)\b")
PARAPET_SELF_LICENSING = re.compile(
    r"\bPARAPET\b(?![- ]owned)[^.]{0,120}?\b(?:released|licensed|distributed)\s+under\b",
    re.IGNORECASE,
)


def _sentences_licensing_parapet_under_another_license(text):
    """Return sentences that license PARAPET itself under a non-Apache license.

    Works on whitespace-flattened sentences rather than physical lines: the
    claim this guards against spanned two source lines in the pre-1.0 README.
    """
    flat = re.sub(r"\s+", " ", text)
    offenders = []
    for sentence in re.split(r"(?<=[.!?])\s+", flat):
        match = NON_APACHE_LICENSE.search(sentence)
        if not match:
            continue
        claim = PARAPET_SELF_LICENSING.search(sentence)
        if claim and claim.end() <= match.start():
            offenders.append(sentence.strip())
    return offenders


# Wording that describes these three snapshots as carrying no license. Written
# in the present tense it is now false; written about the past it is the
# historical record and must stay sayable, so explicitly past-tense sentences
# are exempted rather than banned.
STALE_UNLICENSED_CLAIM = re.compile(
    r"no (?:upstream )?license|license(?: file)? (?:is )?missing|"
    r"missing (?:a )?license|licensing as unresolved|unresolved license|"
    r"none supplied",
    re.IGNORECASE,
)
HISTORICAL_PHRASING = re.compile(
    r"\bpreviously\b|\bno longer\b|\barrived without\b|\bused to\b|"
    r"\bhas since\b|\bbefore that decision\b",
    re.IGNORECASE,
)


def _stale_unlicensed_claims(component, docs):
    """Return ``"doc: sentence"`` for present-tense "unlicensed" claims.

    ``docs`` maps a document name to its text, so the detector can be exercised
    on fixed strings as well as on the repository.
    """
    offenders = []
    for doc, text in docs.items():
        flat = re.sub(r"\s+", " ", text)
        for sentence in re.split(r"(?<=[.!?])\s+", flat):
            if component not in sentence:
                continue
            if not STALE_UNLICENSED_CLAIM.search(sentence):
                continue
            if HISTORICAL_PHRASING.search(sentence):
                continue
            offenders.append(f"{doc}: {sentence.strip()}")
    return offenders


class TestRootLicense:
    def test_root_license_is_the_canonical_apache_2_text(self, repo_root):
        digest = hashlib.md5((repo_root / "LICENSE").read_bytes()).hexdigest()

        assert digest == CANONICAL_APACHE_2_MD5, (
            "the root LICENSE is no longer byte-identical to the canonical "
            "Apache License 2.0 text"
        )

    def test_readme_identifies_the_project_as_apache_2(self, repo_root):
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        assert "Apache-2.0" in readme or "Apache License 2.0" in readme

    @pytest.mark.parametrize("doc", PARAPET_OWNED_DOCS)
    def test_no_parapet_owned_doc_claims_a_non_apache_license_for_parapet(self, repo_root, doc):
        path = repo_root / doc
        if not path.is_file():
            pytest.skip(f"{doc} is not present")

        offenders = _sentences_licensing_parapet_under_another_license(
            path.read_text(encoding="utf-8")
        )

        assert offenders == [], f"{doc} appears to license PARAPET itself under a non-Apache license: {offenders}"

    def test_the_detector_catches_the_historical_mit_wording(self):
        """Proves the check above is not vacuous.

        This is the exact paragraph the README carried before the Apache-2.0
        migration. It is written across two source lines, so a line-scoped
        check would silently miss it.
        """
        historical = (
            "The PARAPET platform (website, documentation, and the integration glue in this\n"
            "repository) is released under the [MIT License](LICENSE). Each vendored project\n"
            "under `projects/` retains its own upstream license; see the `LICENSE` file inside\n"
            "that folder where present."
        )

        offenders = _sentences_licensing_parapet_under_another_license(historical)

        assert len(offenders) == 1
        assert "MIT" in offenders[0]

    def test_the_detector_accepts_correct_third_party_attribution(self):
        """A sentence attributing MIT to a vendored component must not trip it."""
        correct = (
            "PARAPET-owned repository content is licensed under the Apache License 2.0. "
            "MIMIR, vendored under projects/privauditor, is distributed under the MIT License."
        )

        assert _sentences_licensing_parapet_under_another_license(correct) == []


class TestProjectTeamApacheLicenses:
    """The three project directories the project team released under Apache-2.0.

    These files did not exist before that decision; the tests that used to
    assert their absence have been replaced by the assertions here.
    """

    @pytest.mark.parametrize("relpath", PROJECT_TEAM_APACHE_LICENSE_FILES)
    def test_project_level_license_file_exists(self, repo_root, relpath):
        assert (repo_root / relpath).is_file(), (
            f"{relpath} is missing; the project team released this directory's "
            "project-level content under Apache-2.0"
        )

    @pytest.mark.parametrize("relpath", PROJECT_TEAM_APACHE_LICENSE_FILES)
    def test_project_level_license_is_the_canonical_apache_2_text(self, repo_root, relpath):
        path = repo_root / relpath
        digest = hashlib.md5(path.read_bytes()).hexdigest()

        assert digest == CANONICAL_APACHE_2_MD5, (
            f"{relpath} is not byte-identical to the canonical Apache License "
            "2.0 text"
        )

    @pytest.mark.parametrize("relpath", PROJECT_TEAM_APACHE_LICENSE_FILES)
    def test_project_level_license_carries_the_apache_2_markers(self, repo_root, relpath):
        """Reads the file as text, so a hash drift reports something useful."""
        text = (repo_root / relpath).read_text(encoding="utf-8")

        assert "Apache License" in text
        assert "Version 2.0, January 2004" in text
        assert "http://www.apache.org/licenses/" in text

    @pytest.mark.parametrize("relpath", PROJECT_TEAM_APACHE_LICENSE_FILES)
    def test_no_copyright_holder_or_year_was_invented(self, repo_root, relpath):
        """No authoritative repository file names one, so none may be filled in."""
        text = (repo_root / relpath).read_text(encoding="utf-8")

        assert "Copyright [yyyy] [name of copyright owner]" in text

    def test_the_readme_records_apache_2_for_all_three(self, repo_root):
        readme = (repo_root / "README.md").read_text(encoding="utf-8")

        for relpath in PROJECT_TEAM_APACHE_LICENSE_FILES:
            assert relpath in readme, f"README.md does not cite {relpath}"

    @pytest.mark.parametrize(
        "component", ["PerfOrch", "LUNA", "More Than Just Functional"]
    )
    def test_no_parapet_owned_doc_still_calls_these_unlicensed(self, repo_root, component):
        """Guards against a stale "no license supplied" claim surviving a merge."""
        offenders = _stale_unlicensed_claims(
            component,
            {
                doc: (repo_root / doc).read_text(encoding="utf-8")
                for doc in PARAPET_OWNED_DOCS
                if (repo_root / doc).is_file()
            },
        )

        assert offenders == [], (
            f"{component} is Apache-2.0 licensed but is still described as "
            f"unlicensed: {offenders}"
        )

    def test_the_stale_claim_detector_catches_the_pre_decision_wording(self):
        """Proves the check above is not vacuous."""
        historical = {
            "THIRD_PARTY_NOTICES.md": (
                "### LUNA\n\nNo upstream license file was supplied at the artifact\n"
                "root. Treat LUNA's licensing as unresolved."
            )
        }

        offenders = _stale_unlicensed_claims("LUNA", historical)

        assert len(offenders) == 2

    def test_the_stale_claim_detector_allows_the_historical_record(self):
        """Saying the gap *used to* exist is accurate and must stay allowed."""
        historical = {
            "THIRD_PARTY_NOTICES.md": (
                "PerfOrch, LUNA, and More Than Just Functional previously had no "
                "license file in this repository."
            )
        }

        assert _stale_unlicensed_claims("LUNA", historical) == []


class TestThirdPartyLicensesPreserved:
    @pytest.mark.parametrize(("relpath", "marker"), sorted(THIRD_PARTY_LICENSE_FILES.items()))
    def test_upstream_license_file_is_present_and_unreplaced(self, repo_root, relpath, marker):
        path = repo_root / relpath

        assert path.is_file(), f"vendored license {relpath} was removed"
        assert marker in path.read_text(encoding="utf-8", errors="replace"), (
            f"{relpath} no longer contains its upstream license text "
            f"(expected to find {marker!r})"
        )

    def test_the_mit_licensed_component_was_not_relicensed_to_apache(self, repo_root):
        mimir = repo_root / "projects/privauditor/src/mia-attack/mimir/LICENSE"
        text = mimir.read_text(encoding="utf-8")

        assert text.lstrip().startswith("MIT License")
        assert "Apache License" not in text

    def test_the_bsd_licensed_component_was_not_relicensed_to_apache(self, repo_root):
        hmmlearn = repo_root / "projects/luna/src/luna/hmmlearn/LICENSE.txt"
        text = hmmlearn.read_text(encoding="utf-8")

        assert "Redistribution and use in source and binary forms" in text
        assert "Apache License" not in text

    def test_hmmlearn_was_not_swallowed_by_the_luna_project_license(self, repo_root):
        """The sharpest edge of the project-team decision.

        ``projects/luna/LICENSE`` is Apache-2.0 by an explicit project-team
        decision. The nested hmmlearn component is *not* covered by it. A
        well-meaning "make the licenses consistent" pass would copy the one
        over the other; this catches exactly that.
        """
        luna = repo_root / "projects/luna/LICENSE"
        hmmlearn = repo_root / "projects/luna/src/luna/hmmlearn/LICENSE.txt"

        assert luna.is_file() and hmmlearn.is_file()

        luna_digest = hashlib.md5(luna.read_bytes()).hexdigest()
        hmmlearn_digest = hashlib.md5(hmmlearn.read_bytes()).hexdigest()

        assert luna_digest == CANONICAL_APACHE_2_MD5
        assert hmmlearn_digest != luna_digest, (
            "the nested hmmlearn license was overwritten with LUNA's "
            "project-level Apache-2.0 license"
        )

        text = hmmlearn.read_text(encoding="utf-8")
        assert "hmmlearn authors and contributors" in text
        assert "Neither the name of the" in text and "nor the names of its" in text, (
            "the third BSD clause is gone; this no longer reads as BSD-3-Clause"
        )

    def test_no_third_party_license_was_overwritten_with_the_apache_text(self, repo_root):
        """A copied Apache-2.0 file would have the canonical Apache md5.

        The three project-level files added by the project-team decision are
        deliberately not in this dict -- they are *meant* to be that text.
        """
        offenders = []
        for relpath in THIRD_PARTY_LICENSE_FILES:
            if "coquir" in relpath:
                # CoQuIR genuinely ships the canonical Apache-2.0 text upstream.
                continue
            digest = hashlib.md5((repo_root / relpath).read_bytes()).hexdigest()
            if digest == CANONICAL_APACHE_2_MD5:
                offenders.append(relpath)

        assert offenders == []

    def test_the_luna_readme_names_apache_2_not_the_old_fpa_label(self, repo_root):
        """The vendored README's License section must match the file it links to.

        It used to read ``[FPA](LICENSE)`` against a `LICENSE` that did not
        exist. Both halves have since changed, and a label naming a different
        license than the file it points at is exactly the kind of stale claim
        this module exists to catch.
        """
        readme = (repo_root / "projects/luna/README.md").read_text(encoding="utf-8")
        section = readme.split("## License", 1)
        assert len(section) == 2, "projects/luna/README.md lost its License section"
        body = section[1].split("---", 1)[0]

        assert "[Apache License 2.0](LICENSE)" in body, (
            "the LUNA README no longer identifies its project-level license"
        )
        assert "FPA" not in body, "the stale FPA label is back"

    def test_the_luna_readme_still_excludes_the_nested_bsd_component(self, repo_root):
        readme = (repo_root / "projects/luna/README.md").read_text(encoding="utf-8")
        body = readme.split("## License", 1)[1].split("---", 1)[0]

        assert "hmmlearn" in body
        assert "BSD 3-Clause" in body

    def test_the_project_team_decision_added_no_license_outside_its_scope(self, repo_root):
        """Exactly three project-level LICENSE files, in the three named dirs.

        A fourth one appearing under ``projects/`` would mean the decision was
        applied to a directory it does not cover.
        """
        allowed = set(PROJECT_TEAM_APACHE_LICENSE_FILES) | set(THIRD_PARTY_LICENSE_FILES)
        found = {
            str(path.relative_to(repo_root))
            for path in (repo_root / "projects").rglob("*")
            if path.is_file()
            and ("LICENSE" in path.name.upper() or path.name.upper().startswith("COPYING"))
        }

        assert found - allowed == set(), (
            f"undeclared license files under projects/: {sorted(found - allowed)}"
        )
        assert allowed - found == set(), (
            f"declared license files are missing: {sorted(allowed - found)}"
        )


class TestThirdPartyNotices:
    def test_notices_file_exists(self, repo_root):
        assert (repo_root / "THIRD_PARTY_NOTICES.md").is_file()

    @pytest.mark.parametrize(
        "component",
        ["PerfOrch", "CoQuIR", "Metior", "LUNA", "PrivAuditor", "More Than Just Functional"],
    )
    def test_every_vendored_component_is_listed(self, repo_root, component):
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert component in notices

    @pytest.mark.parametrize("relpath", sorted(THIRD_PARTY_LICENSE_FILES))
    def test_every_preserved_license_file_is_referenced(self, repo_root, relpath):
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert relpath in notices, f"{relpath} is preserved but not documented in THIRD_PARTY_NOTICES.md"

    @pytest.mark.parametrize("relpath", PROJECT_TEAM_APACHE_LICENSE_FILES)
    def test_every_project_team_license_file_is_documented(self, repo_root, relpath):
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert relpath in notices, (
            f"{relpath} exists but is not documented in THIRD_PARTY_NOTICES.md"
        )

    def test_the_project_team_decision_and_its_scope_limit_are_recorded(self, repo_root):
        """Replaces the old "flagged as unlicensed" check.

        The decision is only defensible if the notices file says who made it,
        what it covers, and -- the part that matters legally -- what it does
        not.
        """
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert "project team" in notices.lower()
        assert "project-level" in notices.lower()
        assert "hmmlearn" in notices
        assert "BSD 3-Clause" in notices

    def test_the_notices_file_no_longer_calls_the_three_unlicensed(self, repo_root):
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert "No upstream license file was supplied" not in notices
        assert "None supplied in this snapshot" not in notices
        assert "None supplied at the artifact root" not in notices

    def test_the_remaining_licensing_gap_is_still_recorded(self, repo_root):
        """Metior's statement-only license was not resolved by this decision."""
        notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

        assert "Known gaps" in notices
        assert "Metior" in notices
