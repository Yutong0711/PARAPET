"""Functional tests for PerfOrch's agent helper utilities.

``agent/utils.py`` holds the arithmetic that decides whether a candidate
improved on a metric, and the atomic writer used for every result file the
pipeline produces. Both are stdlib-only and deterministic.

``compute_improvement`` is the closest thing in the checked-in repository to
PARAPET's "what did the fix cost" comparison, so its sign convention is
covered explicitly.
"""

from __future__ import annotations

import json
import math

import pytest

from agent.utils import (
    atomic_write_json,
    compute_improvement,
    load_category_file,
    lookup_categories_by_id,
)


class TestComputeImprovement:
    def test_lower_execution_time_is_a_positive_improvement(self):
        improvement = compute_improvement({"execution_time": 100.0}, {"execution_time": 75.0}, "execution_time")

        assert improvement == pytest.approx(0.25)

    def test_higher_execution_time_is_a_negative_improvement(self):
        improvement = compute_improvement({"execution_time": 100.0}, {"execution_time": 125.0}, "execution_time")

        assert improvement == pytest.approx(-0.25)

    def test_memory_uses_the_same_lower_is_better_convention(self):
        assert compute_improvement({"max_memory": 200.0}, {"max_memory": 100.0}, "max_memory") == pytest.approx(0.5)

    def test_cpus_utilized_inverts_the_convention(self):
        # More CPU utilisation is better, so the sign flips for this metric only.
        improvement = compute_improvement({"cpus_utilized": 1.0}, {"cpus_utilized": 1.5}, "cpus_utilized")

        assert improvement == pytest.approx(0.5)

    def test_numeric_strings_are_accepted(self):
        assert compute_improvement({"execution_time": "100"}, {"execution_time": "50"}, "execution_time") == pytest.approx(0.5)

    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ({}, {"execution_time": 1.0}),
            ({"execution_time": 1.0}, {}),
            ({"execution_time": None}, {"execution_time": 1.0}),
            ({"execution_time": "not-a-number"}, {"execution_time": 1.0}),
        ],
    )
    def test_missing_or_unparsable_values_yield_none(self, before, after):
        assert compute_improvement(before, after, "execution_time") is None

    def test_zero_baseline_yields_none_instead_of_dividing_by_zero(self):
        assert compute_improvement({"execution_time": 0.0}, {"execution_time": 1.0}, "execution_time") is None


class TestAtomicWriteJson:
    def test_creates_parent_directories_and_writes_valid_json(self, tmp_path):
        target = tmp_path / "nested" / "deeper" / "result.json"

        atomic_write_json(str(target), {"status": "ok", "runs": [1, 2]})

        assert json.loads(target.read_text(encoding="utf-8")) == {"status": "ok", "runs": [1, 2]}

    def test_leaves_no_temporary_file_behind(self, tmp_path):
        target = tmp_path / "result.json"

        atomic_write_json(str(target), {"a": 1})

        assert not (tmp_path / "result.json.tmp").exists()
        assert [p.name for p in tmp_path.iterdir()] == ["result.json"]

    def test_overwrites_an_existing_file_in_place(self, tmp_path):
        target = tmp_path / "result.json"
        atomic_write_json(str(target), {"generation": 1})

        atomic_write_json(str(target), {"generation": 2})

        assert json.loads(target.read_text(encoding="utf-8")) == {"generation": 2}

    def test_sanitize_floats_replaces_non_finite_values_with_null(self, tmp_path):
        target = tmp_path / "result.json"
        payload = {"time": math.inf, "mem": math.nan, "nested": [float("-inf"), 1.5]}

        atomic_write_json(str(target), payload, sanitize_floats=True)

        # A timed-out or OOM run must serialise as null, not as invalid JSON.
        raw = target.read_text(encoding="utf-8")
        assert "Infinity" not in raw and "NaN" not in raw
        assert json.loads(raw) == {"time": None, "mem": None, "nested": [None, 1.5]}

    def test_without_sanitize_non_finite_values_are_written_unquoted(self, tmp_path):
        target = tmp_path / "result.json"

        atomic_write_json(str(target), {"time": math.inf})

        assert "Infinity" in target.read_text(encoding="utf-8")


class TestCategoryLookup:
    def test_load_category_file_returns_none_for_a_missing_path(self, tmp_path):
        assert load_category_file(str(tmp_path / "absent.json")) is None

    def test_load_category_file_returns_none_for_malformed_json(self, tmp_path):
        broken = tmp_path / "broken.json"
        broken.write_text("{not json", encoding="utf-8")

        assert load_category_file(str(broken)) is None

    def test_lookup_strips_the_language_prefix_from_a_task_id(self, tmp_path, monkeypatch):
        categories = tmp_path / "humanevalpack-category.json"
        categories.write_text(json.dumps({"12": ["Array", "Sorting"]}), encoding="utf-8")
        monkeypatch.setattr(
            "agent.utils.BENCHMARK_CATEGORY_FILES",
            {"humanevalpack": str(categories)},
        )

        # Task ids arrive as "Python/12"; only the numeric part is the key.
        assert lookup_categories_by_id("Python/12", "humanevalpack") == ["Array", "Sorting"]

    def test_lookup_falls_back_to_other_benchmarks_when_the_named_one_misses(self, tmp_path, monkeypatch):
        effibenchx = tmp_path / "effibenchx-category.json"
        effibenchx.write_text(json.dumps({"7": ["Greedy"]}), encoding="utf-8")
        monkeypatch.setattr(
            "agent.utils.BENCHMARK_CATEGORY_FILES",
            {"humanevalpack": str(tmp_path / "absent.json"), "effibenchx": str(effibenchx)},
        )

        assert lookup_categories_by_id("Python/7", "humanevalpack") == ["Greedy"]

    def test_lookup_returns_none_when_the_id_is_absent_everywhere(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "agent.utils.BENCHMARK_CATEGORY_FILES",
            {"humanevalpack": str(tmp_path / "absent.json")},
        )

        assert lookup_categories_by_id("Python/999", "humanevalpack") is None
