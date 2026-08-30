"""Functional tests for PerfOrch's model-selection memory.

``agent/memory.py`` is what decides *which* model the pipeline asks for a
candidate: it replays past generate/fix/refine records and ranks models per
(language, category, metric). It is stdlib-only and deterministic.

The module reads fixed relative paths (``data/memory/memory.json``,
``data/memory/threshold.json``, ``benchmark/*/*-category.json``), so the tests
build a real directory tree in ``tmp_path`` and run from there. That exercises
the file loading as well as the ranking.
"""

from __future__ import annotations

import json

import pytest

from agent.memory import AgentMemory


def _write_workspace(root, *, memory, categories, thresholds=None):
    """Lay out the directory structure AgentMemory expects, and return root."""
    memory_dir = root / "data" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "memory.json").write_text(json.dumps(memory), encoding="utf-8")
    if thresholds is not None:
        (memory_dir / "threshold.json").write_text(json.dumps(thresholds), encoding="utf-8")

    bench_dir = root / "benchmark" / "humanevalpack"
    bench_dir.mkdir(parents=True)
    (bench_dir / "humanevalpack-category.json").write_text(json.dumps(categories), encoding="utf-8")
    return root


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Chdir into a tmp workspace so AgentMemory's relative paths resolve."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


class TestGenerateAndFixAggregation:
    def test_pass_rate_is_the_ratio_of_passing_records(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": False},
                {"stage": "generate", "task_id": "Python/1", "model": "beta", "passed": False},
            ],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha", "beta"], auto_load=True)

        assert memory.generate_data["python-Array-pass_rate"]["alpha"]["pass_rate"] == pytest.approx(2 / 3)
        assert memory.generate_data["python-Array-pass_rate"]["beta"]["pass_rate"] == 0.0

    def test_a_record_is_counted_once_per_category_tag(self, workspace):
        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True}],
            categories={"1": ["Array", "Sorting"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.generate_data["python-Array-pass_rate"]["alpha"]["pass_rate"] == 1.0
        assert memory.generate_data["python-Sorting-pass_rate"]["alpha"]["pass_rate"] == 1.0

    def test_records_without_a_known_category_fall_back_to_unknown(self, workspace):
        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/404", "model": "alpha", "passed": True}],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert "python-Unknown-pass_rate" in memory.generate_data

    def test_stages_are_kept_in_separate_indexes(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True},
                {"stage": "fix", "task_id": "Python/1", "model": "alpha", "passed": False},
            ],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.generate_data["python-Array-pass_rate"]["alpha"]["pass_rate"] == 1.0
        assert memory.fix_data["python-Array-pass_rate"]["alpha"]["pass_rate"] == 0.0

    def test_reloading_does_not_double_count(self, workspace):
        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True}],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        memory.load_data()

        assert memory.generate_data["python-Array-pass_rate"]["alpha"]["pass_rate"] == 1.0


class TestRefineAggregation:
    def test_improvements_accumulate_across_records(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "alpha",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 50.0, "passed": True},
                },
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "alpha",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 80.0, "passed": True},
                },
            ],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        # 0.5 + 0.2
        assert memory.refine_data["python-Array-execution_time"]["alpha"]["sum_improvements"] == pytest.approx(0.7)

    def test_a_candidate_that_did_not_pass_is_discarded(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "alpha",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 10.0, "passed": False},
                }
            ],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.refine_data == {}

    def test_a_regression_registers_the_model_but_adds_nothing(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "alpha",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 150.0, "passed": True},
                }
            ],
            categories={"1": ["Array"]},
        )

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        # The model stays available for tie-breaking with a zero score.
        assert memory.refine_data["python-Array-execution_time"]["alpha"]["sum_improvements"] == 0.0

    def test_improvement_at_or_below_the_threshold_is_treated_as_noise(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "alpha",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 95.0, "passed": True},
                },
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "beta",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 70.0, "passed": True},
                },
            ],
            categories={"1": ["Array"]},
            thresholds={"execution_time": {"python": 0.1}},
        )

        memory = AgentMemory(available_models=["alpha", "beta"], auto_load=True)
        bucket = memory.refine_data["python-Array-execution_time"]

        # alpha's 5% gain is under the 10% noise floor and must not count;
        # beta's 30% gain is above it. This is the measurement-trust rule.
        assert bucket["alpha"]["sum_improvements"] == 0.0
        assert bucket["beta"]["sum_improvements"] == pytest.approx(0.3)


class TestGetTopModels:
    def test_models_are_ranked_by_pass_rate(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": "low", "passed": False},
                {"stage": "generate", "task_id": "Python/1", "model": "low", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "high", "passed": True},
            ],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["low", "high"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "generate", 2) == ["high", "low"]

    def test_ties_break_deterministically_on_model_name(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": "zulu", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True},
            ],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["zulu", "alpha"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "generate", 2) == ["alpha", "zulu"]

    def test_num_models_limits_the_result(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": name, "passed": True}
                for name in ("a", "b", "c")
            ],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["a", "b", "c"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "generate", 2) == ["a", "b"]

    def test_the_allowlist_filters_the_ranking(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {"stage": "generate", "task_id": "Python/1", "model": "allowed", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "blocked", "passed": True},
            ],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["allowed"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "generate", 5) == ["allowed"]

    def test_language_matching_is_case_insensitive(self, workspace):
        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True}],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.get_top_models("PYTHON", ["Array"], "generate", 1) == ["alpha"]

    def test_multi_tag_scores_combine_multiplicatively(self, workspace):
        """A model must be good at *every* tag of a task, not just one.

        beta wins on Array alone, but alpha wins once Sorting is included,
        because per-tag pass rates are multiplied rather than averaged.
        """
        _write_workspace(
            workspace,
            memory=[
                # Array: alpha 0.5, beta 1.0
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True},
                {"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": False},
                {"stage": "generate", "task_id": "Python/1", "model": "beta", "passed": True},
                # Sorting: alpha 1.0, beta 0.25
                {"stage": "generate", "task_id": "Python/2", "model": "alpha", "passed": True},
                {"stage": "generate", "task_id": "Python/2", "model": "beta", "passed": True},
                {"stage": "generate", "task_id": "Python/2", "model": "beta", "passed": False},
                {"stage": "generate", "task_id": "Python/2", "model": "beta", "passed": False},
                {"stage": "generate", "task_id": "Python/2", "model": "beta", "passed": False},
            ],
            categories={"1": ["Array"], "2": ["Sorting"]},
        )
        memory = AgentMemory(available_models=["alpha", "beta"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "generate", 2) == ["beta", "alpha"]
        # alpha 0.5*1.0 = 0.5 beats beta 1.0*0.25 = 0.25.
        assert memory.get_top_models("Python", ["Array", "Sorting"], "generate", 2) == ["alpha", "beta"]

    def test_refine_ranking_uses_summed_improvement(self, workspace):
        _write_workspace(
            workspace,
            memory=[
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "small",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 90.0, "passed": True},
                },
                {
                    "stage": "refine",
                    "task_id": "Python/1",
                    "model": "big",
                    "before": {"execution_time": 100.0},
                    "after": {"execution_time": 40.0, "passed": True},
                },
            ],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["small", "big"], auto_load=True)

        ranked = memory.get_top_models("Python", ["Array"], "refine", 2, metric="execution_time")

        assert ranked == ["big", "small"]

    def test_unknown_stage_returns_an_empty_ranking(self, workspace):
        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True}],
            categories={"1": ["Array"]},
        )
        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.get_top_models("Python", ["Array"], "nonexistent", 1) == []

    def test_missing_memory_file_leaves_the_indexes_empty(self, workspace):
        (workspace / "data" / "memory").mkdir(parents=True)

        memory = AgentMemory(available_models=["alpha"], auto_load=True)

        assert memory.generate_data == {}
        assert memory.get_top_models("Python", ["Array"], "generate", 1) == []

    def test_a_non_list_memory_file_is_rejected_loudly(self, workspace):
        _write_workspace(workspace, memory={"not": "a list"}, categories={"1": ["Array"]})

        with pytest.raises(TypeError, match="must be list"):
            AgentMemory(available_models=["alpha"], auto_load=True)

    def test_the_default_model_list_is_not_mutated_by_an_instance(self, workspace):
        from agent.memory import full_model

        _write_workspace(
            workspace,
            memory=[{"stage": "generate", "task_id": "Python/1", "model": "alpha", "passed": True}],
            categories={"1": ["Array"]},
        )
        snapshot = list(full_model)

        memory = AgentMemory(auto_load=True)
        memory.available_models.append("injected")

        assert full_model == snapshot
