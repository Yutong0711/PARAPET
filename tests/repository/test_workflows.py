"""Repository sanity checks for the GitHub Actions workflows.

STRUCTURAL, NOT FUNCTIONAL. These checks do not run any workflow. They parse
each workflow file and assert the properties PARAPET's release process depends
on -- valid YAML, the documented triggers, least-privilege permissions, no
suppressed failures, no inline secrets, and a Pages deployment that is gated on
validation and restricted to main.

A broken workflow file is invisible until a push, and a workflow that quietly
stops failing is worse than no workflow at all, so both are checked here.
"""

from __future__ import annotations

import re

import pytest
import yaml

WORKFLOWS = ["ci.yml", "pages.yml", "release-check.yml"]

# `on:` is parsed by PyYAML 1.1 semantics as the boolean True, not the string.
ON = True


@pytest.fixture(scope="module")
def workflows(repo_root):
    directory = repo_root / ".github" / "workflows"
    return {path.name: yaml.safe_load(path.read_text(encoding="utf-8")) for path in directory.glob("*.yml")}


@pytest.fixture(scope="module")
def raw_workflows(repo_root):
    directory = repo_root / ".github" / "workflows"
    return {path.name: path.read_text(encoding="utf-8") for path in directory.glob("*.yml")}


class TestAllWorkflows:
    def test_the_expected_workflow_files_are_present(self, workflows):
        assert set(workflows) == set(WORKFLOWS)

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_workflow_is_valid_yaml_with_triggers_and_jobs(self, workflows, name):
        document = workflows[name]

        assert isinstance(document, dict)
        assert document.get("name")
        assert document.get(ON), f"{name} declares no triggers"
        assert document.get("jobs"), f"{name} declares no jobs"

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_every_job_pins_a_runner_and_has_steps(self, workflows, name):
        for job_name, job in workflows[name]["jobs"].items():
            assert job.get("runs-on"), f"{name}:{job_name} has no runs-on"
            assert job.get("steps"), f"{name}:{job_name} has no steps"

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_no_step_or_job_suppresses_failures(self, workflows, name):
        """continue-on-error would let a claimed validation pass while broken."""
        offenders = []
        for job_name, job in workflows[name]["jobs"].items():
            if job.get("continue-on-error"):
                offenders.append(f"{name}:{job_name}")
            for step in job["steps"]:
                if step.get("continue-on-error"):
                    offenders.append(f"{name}:{job_name}:{step.get('name', '?')}")

        assert offenders == []

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_workflow_declares_least_privilege_permissions(self, workflows, name):
        permissions = workflows[name].get("permissions")

        assert permissions is not None, f"{name} does not declare permissions"
        assert permissions.get("contents") == "read", f"{name} grants more than read on contents"

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_workflow_references_no_secrets(self, raw_workflows, name):
        assert "secrets." not in raw_workflows[name]

    @pytest.mark.parametrize("name", WORKFLOWS)
    def test_every_action_is_pinned_to_a_major_version(self, workflows, name):
        unpinned = []
        for job in workflows[name]["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses")
                if uses and not re.search(r"@v\d+$", uses) and not re.search(r"@[0-9a-f]{40}$", uses):
                    unpinned.append(uses)

        assert unpinned == [], f"{name} uses unpinned actions: {unpinned}"


class TestCiWorkflow:
    @pytest.fixture(scope="class")
    def ci(self, repo_root):
        return yaml.safe_load((repo_root / ".github/workflows/ci.yml").read_text(encoding="utf-8"))

    def test_it_runs_on_pull_requests_targeting_main(self, ci):
        assert ci[ON]["pull_request"]["branches"] == ["main"]

    def test_it_runs_on_pushes_to_main(self, ci):
        assert ci[ON]["push"]["branches"] == ["main"]

    def test_it_can_be_dispatched_manually(self, ci):
        assert "workflow_dispatch" in ci[ON]

    def test_it_defines_the_three_documented_jobs(self, ci):
        assert set(ci["jobs"]) == {"component-tests", "jvm-smoke", "repository-sanity"}

    @pytest.mark.parametrize(
        ("job", "expected_paths"),
        [
            ("component-tests", ["tests/perforch", "tests/more_than_just_functional"]),
            ("jvm-smoke", ["tests/perforch"]),
            ("repository-sanity", ["tests/repository", "tests/website"]),
        ],
    )
    def test_each_job_actually_runs_pytest_over_its_tests(self, ci, job, expected_paths):
        """Guards against a job that claims to validate something but does not."""
        commands = " ".join(step.get("run", "") for step in ci["jobs"][job]["steps"])

        assert "pytest" in commands
        for path in expected_paths:
            assert path in commands

    def test_the_jvm_job_installs_a_jdk_and_selects_the_jvm_marker(self, ci):
        job = ci["jobs"]["jvm-smoke"]
        uses = [step.get("uses", "") for step in job["steps"]]
        commands = " ".join(step.get("run", "") for step in job["steps"])

        assert any("setup-java" in u for u in uses)
        assert "-m jvm" in commands

    def test_the_component_job_excludes_the_jvm_marker(self, ci):
        commands = " ".join(step.get("run", "") for step in ci["jobs"]["component-tests"]["steps"])

        assert 'not jvm' in commands

    def test_dependency_installation_is_cached(self, ci):
        for job_name, job in ci["jobs"].items():
            setup = [s for s in job["steps"] if "setup-python" in s.get("uses", "")]
            assert setup, f"{job_name} does not set up Python"
            assert setup[0]["with"].get("cache") == "pip", f"{job_name} does not cache pip downloads"


class TestPagesWorkflow:
    @pytest.fixture(scope="class")
    def pages(self, repo_root):
        return yaml.safe_load((repo_root / ".github/workflows/pages.yml").read_text(encoding="utf-8"))

    def test_deployment_only_runs_from_main(self, pages):
        assert pages[ON]["push"]["branches"] == ["main"]
        assert "pull_request" not in pages[ON]

    def test_deployment_depends_on_validation(self, pages):
        assert pages["jobs"]["deploy"]["needs"] == "validate"

    def test_the_validate_job_runs_the_website_checks(self, pages):
        commands = " ".join(step.get("run", "") for step in pages["jobs"]["validate"]["steps"])

        assert "pytest" in commands
        assert "tests/website" in commands

    def test_pages_write_permission_is_granted_only_here(self, workflows):
        for name, document in workflows.items():
            has_pages_write = document.get("permissions", {}).get("pages") == "write"
            assert has_pages_write == (name == "pages.yml"), (
                f"{name} should not hold pages:write"
            )

    def test_deployment_uses_the_official_pages_actions(self, pages):
        uses = [step.get("uses", "") for step in pages["jobs"]["deploy"]["steps"]]

        assert any("actions/upload-pages-artifact" in u for u in uses)
        assert any("actions/deploy-pages" in u for u in uses)


class TestReleaseCheckWorkflow:
    @pytest.fixture(scope="class")
    def release(self, repo_root):
        return yaml.safe_load((repo_root / ".github/workflows/release-check.yml").read_text(encoding="utf-8"))

    def test_it_triggers_on_version_tags(self, release):
        assert release[ON]["push"]["tags"] == ["v*"]

    def test_it_verifies_the_tag_against_the_version_file(self, release):
        commands = " ".join(step.get("run", "") for step in release["jobs"]["validate-release"]["steps"])

        assert "VERSION" in commands

    def test_it_runs_the_documented_validation_entrypoint(self, release):
        commands = " ".join(step.get("run", "") for step in release["jobs"]["validate-release"]["steps"])

        assert "scripts/run_tests.sh" in commands

    def test_it_neither_publishes_a_release_nor_writes_to_the_repository(self, repo_root, release):
        raw = (repo_root / ".github/workflows/release-check.yml").read_text(encoding="utf-8")

        # Creating the tag and the GitHub Release is a manual, human step.
        assert release["permissions"].get("contents") == "read"
        for forbidden in ("softprops/action-gh-release", "gh release create", "create-release", "git push"):
            assert forbidden not in raw


class TestTestRunnerScript:
    def test_the_runner_script_exists_and_is_executable(self, repo_root):
        import os

        script = repo_root / "scripts/run_tests.sh"

        assert script.is_file()
        assert os.access(script, os.X_OK), "scripts/run_tests.sh is not executable"

    def test_the_runner_covers_every_test_directory(self, repo_root):
        script = (repo_root / "scripts/run_tests.sh").read_text(encoding="utf-8")

        for directory in ("tests/perforch", "tests/more_than_just_functional", "tests/repository", "tests/website"):
            assert directory in script, f"{directory} is not run by scripts/run_tests.sh"
