"""The chain: budgets, stage skipping, and the record it produces."""

import json

import pytest

from parapet_cli.budget import describe, load_budget, write_budget_template
from parapet_cli.cli import main
from parapet_cli.pipeline import run_pipeline

EXAMPLE = """\
key,summary,description
DEMO-1,Reads are slow,"Loading the dump takes most of the time, about 40 minutes."
DEMO-2,Add a flag,"It would be useful to add a --verbose flag."
"""

BEFORE = """\
method,time,own_time,count
acme.Loader#load,1000.0,40.0,50000
acme.Cache#get,900.0,900.0,50000
"""

AFTER = """\
method,time,own_time,count
acme.Loader#load,1120.0,41.0,50000
acme.Cache#get,1019.0,1019.0,50000
"""

SOURCE = """\
package acme;
public class Loader {
    private Cache cache;
    public byte[] load(String name) { return cache.get(name); }
}
"""
CACHE = """\
package acme;
public class Cache {
    public byte[] get(String key) { return new byte[0]; }
}
"""


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "issues.csv").write_text(EXAMPLE, encoding="utf-8")
    (tmp_path / "before.csv").write_text(BEFORE, encoding="utf-8")
    (tmp_path / "after.csv").write_text(AFTER, encoding="utf-8")
    source = tmp_path / "src" / "acme"
    source.mkdir(parents=True)
    (source / "Loader.java").write_text(SOURCE, encoding="utf-8")
    (source / "Cache.java").write_text(CACHE, encoding="utf-8")
    return tmp_path


# --- budgets ---------------------------------------------------------------

def test_the_template_is_loadable_as_written(tmp_path):
    path = write_budget_template(tmp_path, "acme")
    budget = load_budget(path)
    limits = getattr(budget, "limits", None) or budget["limits"]
    assert "latency" in limits


def test_a_budget_without_an_authority_is_rejected(tmp_path):
    path = tmp_path / "b.yaml"
    path.write_text("project: x\nlimits:\n  latency: \"5%\"\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_budget(path)
    assert "authority" in str(excinfo.value)


def test_a_budget_without_limits_is_rejected(tmp_path):
    path = tmp_path / "b.yaml"
    path.write_text("project: x\nauthority: someone\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_budget(path)


def test_describe_warns_when_no_workload_is_declared(tmp_path):
    path = tmp_path / "b.yaml"
    path.write_text("project: x\nauthority: two maintainers\n"
                    "limits:\n  latency: \"5%\"\n", encoding="utf-8")
    text = describe(load_budget(path))
    assert "no workloads declared" in text


# --- the pipeline ----------------------------------------------------------

def test_triage_alone(workspace):
    result = run_pipeline(out=workspace / "records",
                          issues=workspace / "issues.csv",
                          record_id="r")
    triage = result.stage("triage")
    assert triage.ran and "matched" in triage.detail
    assert not result.stage("scope").ran
    assert result.verdict == "unscored"
    assert result.record_path.exists()


def test_a_skipped_stage_says_what_is_missing(workspace):
    result = run_pipeline(out=workspace / "records", record_id="r")
    assert "no --issues" in result.stage("triage").detail
    assert "no --repo" in result.stage("scope").detail
    assert "missing" in result.stage("attrib").detail
    assert "no --budget" in result.stage("budget").detail


def test_no_exposure_produces_a_warning(workspace):
    result = run_pipeline(out=workspace / "records",
                          before_profile=workspace / "before.csv",
                          after_profile=workspace / "after.csv",
                          source=workspace / "src",
                          changed_methods=["acme.Loader#load"],
                          record_id="r")
    assert any("no exposure recorded" in w for w in result.warnings)


def test_attribution_runs_from_source(workspace):
    result = run_pipeline(out=workspace / "records",
                          before_profile=workspace / "before.csv",
                          after_profile=workspace / "after.csv",
                          source=workspace / "src",
                          changed_methods=["acme.Loader#load"],
                          record_id="r")
    attrib = result.stage("attrib")
    assert attrib.ran
    assert "landed" in attrib.detail


def test_attribution_needs_the_changed_methods(workspace):
    result = run_pipeline(out=workspace / "records",
                          before_profile=workspace / "before.csv",
                          after_profile=workspace / "after.csv",
                          source=workspace / "src",
                          record_id="r")
    assert not result.stage("attrib").ran
    assert "changed methods" in result.stage("attrib").detail


def test_a_single_sample_cost_stays_unscored(workspace):
    budget = workspace / "budget.yaml"
    budget.write_text("project: x\nauthority: two maintainers\n"
                      "limits:\n  latency: \"50%\"\nbinding: [latency]\n"
                      "workloads: [bench]\n", encoding="utf-8")
    result = run_pipeline(out=workspace / "records",
                          before_profile=workspace / "before.csv",
                          after_profile=workspace / "after.csv",
                          source=workspace / "src",
                          changed_methods=["acme.Loader#load"],
                          budget_path=budget, record_id="r")
    # The cost is well inside a 50% limit, and it still does not admit,
    # because one sample has no interval.
    assert result.verdict == "unscored"


def test_the_record_can_be_read_back(workspace, capsys):
    run_pipeline(out=workspace / "records",
                 issues=workspace / "issues.csv",
                 before_profile=workspace / "before.csv",
                 after_profile=workspace / "after.csv",
                 source=workspace / "src",
                 changed_methods=["acme.Loader#load"],
                 record_id="r")
    assert main(["show", str(workspace / "records" / "r.json")]) == 0
    out = capsys.readouterr().out
    assert "record r" in out
    assert "the cost landed" in out


# --- command line ----------------------------------------------------------

def test_cli_init_writes_a_budget(tmp_path, capsys):
    assert main(["init", "--path", str(tmp_path / "b.yaml"),
                 "--project", "acme"]) == 0
    assert (tmp_path / "b.yaml").exists()
    assert "authority" in capsys.readouterr().out


def test_cli_doctor_lists_the_components(capsys):
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "parapet-record" in out and "parapet-triage" in out


def test_cli_run_json(workspace, capsys):
    assert main(["run", "--issues", str(workspace / "issues.csv"),
                 "--out", str(workspace / "records"),
                 "--record-id", "r", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "unscored"
    assert {stage["name"] for stage in payload["stages"]} == {
        "triage", "scope", "attrib", "budget"}


def test_cli_fail_unless_admitted_is_a_gate(workspace):
    assert main(["run", "--issues", str(workspace / "issues.csv"),
                 "--out", str(workspace / "records"), "--record-id", "r",
                 "--fail-unless-admitted"]) == 3
