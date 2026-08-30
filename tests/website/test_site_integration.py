"""Integration checks for the PARAPET static website.

STRUCTURAL / INTEGRATION, NOT FUNCTIONAL JAVASCRIPT TESTING. No browser or DOM
is instantiated here, so these checks do **not** prove that ``script.js``
behaves correctly at runtime. What they do prove is that the three independent
pieces of the site agree with each other:

  1. every element ``script.js`` reaches for actually exists in ``index.html``;
  2. every local asset ``index.html`` references exists on disk;
  3. every local asset the page needs is staged by the Pages deploy workflow;
  4. every in-page ``#anchor`` resolves to a real ``id``.

Each of those has a concrete failure mode -- renaming ``#site-nav`` silently
breaks the mobile menu, and adding a stylesheet without updating the deploy
workflow ships a page with no styling -- and none is caught by any other test.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

import pytest

SITE_FILES = ("index.html", "styles.css", "script.js", ".nojekyll")

# Selectors script.js resolves at load time; a miss means a broken interaction.
REQUIRED_SELECTORS = {
    ".menu-button": ("class", "menu-button"),
    "#site-nav": ("id", "site-nav"),
    "#year": ("id", "year"),
}


class _SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.classes = set()
        self.local_assets = set()
        self.internal_anchors = set()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        for name in (attributes.get("class") or "").split():
            self.classes.add(name)
        for attribute in ("href", "src"):
            value = attributes.get(attribute)
            if not value:
                continue
            if value.startswith("#"):
                if len(value) > 1:
                    self.internal_anchors.add(value[1:])
            elif not re.match(r"^(https?:)?//|^mailto:|^data:", value):
                self.local_assets.add(value.split("?", 1)[0].split("#", 1)[0])


@pytest.fixture(scope="module")
def site(repo_root):
    parser = _SiteParser()
    parser.feed((repo_root / "index.html").read_text(encoding="utf-8"))
    return parser


class TestSiteAssets:
    @pytest.mark.parametrize("name", SITE_FILES)
    def test_site_file_is_present(self, repo_root, name):
        assert (repo_root / name).is_file()

    def test_every_local_asset_referenced_by_the_page_exists(self, repo_root, site):
        missing = [asset for asset in site.local_assets if not (repo_root / asset).exists()]

        assert missing == [], f"index.html references missing local assets: {missing}"

    def test_the_page_loads_the_stylesheet_and_the_script(self, site):
        assert "styles.css" in site.local_assets
        assert "script.js" in site.local_assets

    def test_nojekyll_is_present_so_pages_serves_files_verbatim(self, repo_root):
        assert (repo_root / ".nojekyll").is_file()


class TestHtmlJavaScriptContract:
    @pytest.mark.parametrize("selector", sorted(REQUIRED_SELECTORS))
    def test_script_still_queries_the_selector(self, repo_root, selector):
        """Guards the test itself: if script.js stops using a selector, this
        list is stale and must be updated rather than silently over-asserting."""
        script = (repo_root / "script.js").read_text(encoding="utf-8")

        assert f"'{selector}'" in script or f'"{selector}"' in script

    @pytest.mark.parametrize(("selector", "expectation"), sorted(REQUIRED_SELECTORS.items()))
    def test_the_page_provides_every_element_the_script_queries(self, site, selector, expectation):
        kind, name = expectation
        available = site.ids if kind == "id" else site.classes

        assert name in available, f"script.js queries {selector} but index.html has no such element"

    def test_the_menu_button_controls_the_nav_it_toggles(self, site):
        buttons = [attrs for tag, attrs in site.tags if "menu-button" in (attrs.get("class") or "")]

        assert len(buttons) == 1
        # script.js flips aria-expanded on this button and toggles #site-nav;
        # aria-controls must name that same element or the two disagree.
        assert buttons[0].get("aria-controls") == "site-nav"
        assert buttons[0].get("aria-expanded") == "false"

    def test_the_open_class_toggled_by_the_script_is_styled(self, repo_root):
        script = (repo_root / "script.js").read_text(encoding="utf-8")
        styles = (repo_root / "styles.css").read_text(encoding="utf-8")

        assert "'open'" in script
        # Toggling a class no stylesheet defines would leave the menu invisible.
        assert re.search(r"\.open\b", styles)

    def test_the_nav_contains_links_for_the_script_to_bind(self, site, repo_root):
        html = (repo_root / "index.html").read_text(encoding="utf-8")
        nav = re.search(r'<nav id="site-nav".*?</nav>', html, re.S)

        assert nav is not None
        assert nav.group(0).count("<a ") >= 1


class TestInternalAnchors:
    def test_every_in_page_anchor_resolves_to_an_element_id(self, site):
        dangling = sorted(site.internal_anchors - site.ids)

        assert dangling == [], f"index.html has anchors with no matching id: {dangling}"

    @pytest.mark.parametrize("anchor", ["top", "main", "projects", "ecosystem", "roadmap"])
    def test_the_navigation_targets_still_exist(self, site, anchor):
        assert anchor in site.ids


class TestPagesDeployManifest:
    @pytest.fixture(scope="class")
    def workflow(self, repo_root):
        return (repo_root / ".github/workflows/pages.yml").read_text(encoding="utf-8")

    def test_the_deploy_workflow_exists(self, repo_root):
        assert (repo_root / ".github/workflows/pages.yml").is_file()

    def test_every_asset_the_page_needs_is_staged_for_deployment(self, site, workflow):
        """The workflow copies an explicit file list; an unstaged asset 404s."""
        unstaged = [asset for asset in sorted(site.local_assets) if asset not in workflow]

        assert unstaged == [], f"assets referenced by index.html but not staged by pages.yml: {unstaged}"

    @pytest.mark.parametrize("name", SITE_FILES)
    def test_each_site_file_is_named_by_the_workflow(self, workflow, name):
        assert name in workflow

    def test_deployment_is_restricted_to_the_main_branch(self, workflow):
        assert "branches: [main]" in workflow

    def test_deployment_does_not_run_on_pull_requests(self, workflow):
        assert "pull_request" not in workflow
