"""The record schema, and the budget check that decides on it."""

import json

import pytest

from parapet_record import (Budget, CostMeasure, Exposure, HardeningRecord,
                            Provenance, ReviewCost, ToolResult, content_digest,
                            environment_profile, file_digest, load_record,
                            merge_results, new_provenance, save_record)
from parapet_record.schema import BudgetError, check_budget


def _cost(**kwargs):
    defaults = dict(dimension="latency", value=105.0, unit="ms", baseline=100.0,
                    workload="bench/read")
    defaults.update(kwargs)
    return CostMeasure(**defaults)


# --- budget parsing --------------------------------------------------------

def test_limits_carry_their_unit():
    budget = Budget(limits={"latency": "5%", "memory": "64mb", "cpu": "1.2x"})
    assert budget.parse_limit("latency") == (5.0, "%")
    assert budget.parse_limit("memory") == (64.0, "mb")
    assert budget.parse_limit("cpu") == (1.2, "x")


def test_an_undeclared_dimension_returns_none():
    assert Budget(limits={"latency": "5%"}).parse_limit("memory") is None


def test_a_limit_without_a_unit_is_rejected():
    with pytest.raises(BudgetError) as excinfo:
        Budget(limits={"latency": "5"}).parse_limit("latency")
    assert "readable unit" in str(excinfo.value)


def test_an_unknown_unit_is_rejected():
    with pytest.raises(BudgetError):
        Budget(limits={"latency": "5furlongs"}).parse_limit("latency")


# --- the budget check ------------------------------------------------------

def test_a_relative_limit_is_read_against_the_baseline():
    budget = Budget(limits={"latency": "10%"})
    check = check_budget(budget, _cost(value=105.0, baseline=100.0))
    assert check.fits


def test_a_relative_limit_needs_a_baseline():
    budget = Budget(limits={"latency": "10%"})
    check = check_budget(budget, _cost(value=105.0, baseline=None))
    assert not check.fits
    assert "baseline" in check.reason


def test_the_whole_interval_must_fit():
    budget = Budget(limits={"latency": "5%"})
    check = check_budget(budget, _cost(value=104.0, baseline=100.0,
                                       interval_low=102.0, interval_high=106.0))
    assert check.fits                 # the point estimate is inside
    assert check.interval_fits is False   # the interval is not


def test_an_absolute_limit_compares_added_cost():
    budget = Budget(limits={"memory": "64mb"})
    check = check_budget(budget, CostMeasure("memory", 200.0, "mb", baseline=150.0))
    assert check.fits and check.overrun == 0.0


def test_comparing_across_units_raises_rather_than_guessing():
    budget = Budget(limits={"latency": "20ms"})
    with pytest.raises(BudgetError) as excinfo:
        check_budget(budget, CostMeasure("latency", 2.0, "s", baseline=1.0))
    assert "convert" in str(excinfo.value)


def test_an_undeclared_dimension_is_a_non_decision():
    budget = Budget(limits={"latency": "5%"})
    check = check_budget(budget, CostMeasure("memory", 10.0, "mb"))
    assert check.fits is True
    assert check.interval_fits is None
    assert "cannot decide" in check.reason


# --- the verdict -----------------------------------------------------------

def test_no_checks_means_unscored():
    assert HardeningRecord().decide() == "unscored"


def test_a_cost_without_an_interval_cannot_admit():
    budget = Budget(limits={"latency": "5%"})
    cost = _cost(value=101.0, baseline=100.0)      # no interval
    record = HardeningRecord(budget=budget, costs=[cost])
    record.budget_checks.append(check_budget(budget, cost))
    assert record.decide() == "unscored"
    assert any("no interval" in warning for warning in record.warnings)


def test_a_fitting_interval_admits():
    budget = Budget(limits={"latency": "10%"})
    cost = _cost(value=104.0, baseline=100.0, interval_low=103.0,
                 interval_high=105.0)
    record = HardeningRecord(budget=budget, costs=[cost])
    record.budget_checks.append(check_budget(budget, cost))
    assert record.decide() == "admitted"


def test_an_overrunning_interval_overruns():
    budget = Budget(limits={"latency": "1%"})
    cost = _cost(value=104.0, baseline=100.0, interval_low=103.0,
                 interval_high=105.0)
    record = HardeningRecord(budget=budget, costs=[cost])
    record.budget_checks.append(check_budget(budget, cost))
    assert record.decide() == "overrun"


def test_one_overrun_among_several_is_enough():
    budget = Budget(limits={"latency": "10%", "memory": "1%"})
    good = _cost(interval_low=104.0, interval_high=105.0)
    bad = CostMeasure("memory", 200.0, "mb", baseline=100.0,
                      interval_low=190.0, interval_high=210.0)
    record = HardeningRecord(budget=budget, costs=[good, bad])
    record.budget_checks.extend([check_budget(budget, good),
                                 check_budget(budget, bad)])
    assert record.decide() == "overrun"


# --- derived fields --------------------------------------------------------

def test_relative_change():
    assert _cost(value=110.0, baseline=100.0).relative_change == pytest.approx(0.1)
    assert _cost(baseline=0).relative_change is None


def test_an_exposure_knows_whether_it_can_be_verified():
    assert not Exposure("X").has_reproducer
    assert Exposure("X", reproducer="crash.bin").has_reproducer


# --- provenance ------------------------------------------------------------

def test_content_and_file_digests_agree(tmp_path):
    path = tmp_path / "a.txt"
    path.write_text("hello", encoding="utf-8")
    assert file_digest(path) == content_digest("hello")
    assert file_digest(path).startswith("sha256:")


def test_environment_profile_names_the_machine():
    profile = environment_profile()
    assert "python" in profile and "platform" in profile


def test_new_provenance_hashes_every_input(tmp_path):
    path = tmp_path / "patterns.yaml"
    path.write_text("patterns: []", encoding="utf-8")
    provenance = new_provenance("t", "1.0",
                                inputs={"patterns": path, "text": "inline"})
    assert provenance.inputs["patterns"].startswith("sha256:")
    assert provenance.inputs["text"] == content_digest("inline")
    assert provenance.environment


def test_a_record_knows_whether_it_is_reproducible():
    record = HardeningRecord()
    assert not record.reproducible
    record.add(ToolResult("t", new_provenance("t", "1.0",
                                              inputs={"x": "y"})))
    assert record.reproducible


def test_a_component_without_inputs_makes_the_record_unreproducible():
    record = HardeningRecord()
    record.add(ToolResult("t", Provenance(tool="t", tool_version="1.0")))
    assert not record.reproducible


# --- serialisation ---------------------------------------------------------

def test_roundtrip(tmp_path):
    budget = Budget(project="acme", limits={"latency": "5%"}, binding=["latency"],
                    authority="two maintainers")
    cost = _cost(interval_low=104.0, interval_high=105.0)
    record = HardeningRecord(record_id="r1", exposure=Exposure("E-1", kind="security"),
                             change_ref="abc123", budget=budget, costs=[cost],
                             review_cost=ReviewCost(n_production_files=4,
                                                    scope="design-level"))
    record.budget_checks.append(check_budget(budget, cost))
    record.decide()

    path = save_record(record, tmp_path / "r1.json")
    restored = load_record(path)
    assert restored.record_id == "r1"
    assert restored.exposure.identifier == "E-1"
    assert restored.budget.limits == {"latency": "5%"}
    assert restored.review_cost.scope == "design-level"
    assert restored.verdict == record.verdict


def test_a_record_from_an_incompatible_schema_is_refused(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps({"schema_version": "0.9.0"}), encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_record(path)
    assert "not compatible" in str(excinfo.value)


def test_merging_components_folds_their_payloads():
    record = HardeningRecord(record_id="r")
    provenance = new_provenance("t", "1.0", inputs={"a": "b"})
    merged = merge_results(record, [
        ToolResult("parapet-triage", provenance,
                   payload={"exposure": {"identifier": "E-1"}}),
        ToolResult("parapet-scope", provenance,
                   payload={"review_cost": {"scope": "localized"}}),
    ])
    assert merged.exposure.identifier == "E-1"
    assert merged.review_cost.scope == "localized"


def test_two_components_writing_the_same_attribution_key_is_flagged():
    record = HardeningRecord()
    provenance = new_provenance("t", "1.0", inputs={"a": "b"})
    merge_results(record, [
        ToolResult("a", provenance, payload={"attribution": {"where": "here"}}),
        ToolResult("b", provenance, payload={"attribution": {"where": "below"}}),
    ])
    assert any("re-wrote attribution keys" in w for w in record.warnings)
