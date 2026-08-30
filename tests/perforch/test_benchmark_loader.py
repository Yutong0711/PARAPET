"""Functional tests for PerfOrch's benchmark ingestion.

``benchmark_loader.py`` reads the EffiBenchX (gzipped JSONL) and HumanEvalPack
(plain JSONL) problem sets and indexes them by ``task_id``. The benchmark data
itself is not vendored -- upstream ships ~16 MB of it -- so these tests build
small files in the format the loader documents and check that it parses them,
picks the right path per benchmark, and reports lookup failures.
"""

from __future__ import annotations

import gzip
import json

import pytest

from benchmark_loader import BenchmarkLoader


def _write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _write_jsonl_gz(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


class TestHumanEvalPack:
    def test_plain_jsonl_is_parsed_and_indexed(self, tmp_path):
        _write_jsonl(
            tmp_path / "humanevalpack" / "humanevalpack-python.jsonl",
            [{"task_id": "Python/0", "prompt": "def a():"}, {"task_id": "Python/1", "prompt": "def b():"}],
        )

        loader = BenchmarkLoader("humanevalpack", "Python", base_dir=str(tmp_path))

        assert len(loader.data) == 2
        assert loader.get_problem_by_task_id("Python/1")["prompt"] == "def b():"

    def test_language_is_lowercased_in_the_resolved_path(self, tmp_path):
        _write_jsonl(tmp_path / "humanevalpack" / "humanevalpack-cpp.jsonl", [{"task_id": "CPP/0"}])

        loader = BenchmarkLoader("humanevalpack", "CPP", base_dir=str(tmp_path))

        assert loader.json_path.endswith("humanevalpack-cpp.jsonl")

    def test_benchmark_name_is_case_insensitive(self, tmp_path):
        _write_jsonl(tmp_path / "humanevalpack" / "humanevalpack-go.jsonl", [{"task_id": "Go/0"}])

        loader = BenchmarkLoader("HumanEvalPack", "Go", base_dir=str(tmp_path))

        assert loader.benchmark_name == "humanevalpack"


class TestEffiBenchX:
    def test_gzipped_jsonl_is_decompressed_and_parsed(self, tmp_path):
        _write_jsonl_gz(
            tmp_path / "effibenchx" / "effibenchx-rust.jsonl.gz",
            [{"task_id": "Rust/5", "canonical_solution": "1"}],
        )

        loader = BenchmarkLoader("effibenchx", "Rust", base_dir=str(tmp_path))

        assert loader.get_problem_by_task_id("Rust/5")["canonical_solution"] == "1"

    def test_the_derived_filename_strips_every_extension(self, tmp_path):
        _write_jsonl_gz(tmp_path / "effibenchx" / "effibenchx-java.jsonl.gz", [{"task_id": "Java/1"}])

        loader = BenchmarkLoader("effibenchx", "Java", base_dir=str(tmp_path))

        assert loader.filename == "effibenchx-java"


class TestErrorHandling:
    def test_an_unknown_benchmark_is_rejected_before_any_file_access(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown benchmark"):
            BenchmarkLoader("not-a-benchmark", "Python", base_dir=str(tmp_path))

    def test_a_missing_task_id_raises_with_the_id_in_the_message(self, tmp_path):
        _write_jsonl(tmp_path / "humanevalpack" / "humanevalpack-python.jsonl", [{"task_id": "Python/0"}])
        loader = BenchmarkLoader("humanevalpack", "Python", base_dir=str(tmp_path))

        with pytest.raises(ValueError, match="Python/99"):
            loader.get_problem_by_task_id("Python/99")

    def test_records_without_a_task_id_are_kept_but_not_indexed(self, tmp_path):
        _write_jsonl(
            tmp_path / "humanevalpack" / "humanevalpack-python.jsonl",
            [{"prompt": "orphan"}, {"task_id": "Python/0"}],
        )

        loader = BenchmarkLoader("humanevalpack", "Python", base_dir=str(tmp_path))

        assert len(loader.data) == 2
        assert loader.get_problem_by_task_id("Python/0")["task_id"] == "Python/0"
        with pytest.raises(ValueError):
            loader.get_problem_by_task_id("orphan")

    def test_a_missing_benchmark_file_surfaces_as_filenotfound(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            BenchmarkLoader("humanevalpack", "Python", base_dir=str(tmp_path / "absent"))
