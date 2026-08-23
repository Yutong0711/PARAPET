"""Classification, ingestion and the command line."""

import json

import pytest

from parapet_triage import (DEFAULT_ISSUE_THRESHOLD, DEFAULT_SENTENCE_THRESHOLD,
                            Triager, load_pattern_set, load_reports)
from parapet_triage.classify import DEFAULT_WEIGHT
from parapet_triage.cli import main
from parapet_triage.sources import Report, detect_format, from_osv

SLOW = ("Parsing is slow. Loading a 4 MB document takes 30 seconds, and "
        "profiling shows an unnecessary copy in the inner loop.")
BORING = ("Rename the config flag. The old name does not match the other "
          "subcommands, so update the docs too.")


@pytest.fixture(scope="module")
def triager():
    return Triager()


# --- classification --------------------------------------------------------

def test_a_performance_report_matches(triager):
    verdict = triager.classify_text(SLOW, "PROJ-1")
    assert verdict.is_match
    assert verdict.patterns
    assert 0.0 <= verdict.confidence <= 1.0


def test_an_unrelated_report_does_not_match(triager):
    assert not triager.classify_text(BORING, "PROJ-2").is_match


def test_the_verdict_carries_the_sentences_that_produced_it(triager):
    verdict = triager.classify_text(SLOW, "PROJ-1")
    assert verdict.matching_sentences
    assert all(item.patterns for item in verdict.matching_sentences)


def test_explain_names_the_patterns(triager):
    text = triager.classify_text(SLOW, "PROJ-1").explain()
    assert "PROJ-1" in text and "match" in text
    assert any(name in text for name in ("speed", "spend_time", "duration"))


def test_explain_says_so_when_nothing_matched(triager):
    assert "no match" in triager.classify_text(BORING, "PROJ-2").explain()


def test_one_strong_sentence_beats_many_weak_ones(triager):
    """Corroboration adds less than the first piece of evidence.

    Without the diminishing term, a long report full of borderline
    sentences would outscore a short report that states the problem
    outright, which is backwards.
    """
    strong = triager.classify_text(SLOW, "a")
    padded = triager.classify_text(BORING + " " + BORING + " " + BORING, "b")
    assert strong.score > padded.score


def test_empty_text_is_a_clean_no_match(triager):
    verdict = triager.classify_text("", "empty")
    assert not verdict.is_match and verdict.sentences == []


def test_an_unweighted_pattern_can_match_alone():
    """The relation that makes a hand-written pattern set usable.

    ``precision`` is optional, so every set a user writes is unweighted and
    each hit counts DEFAULT_WEIGHT. If that falls below the sentence
    threshold, no such set can ever fire on a single pattern, and nothing
    in the output says why. This pins the three constants together.
    """
    assert DEFAULT_WEIGHT >= DEFAULT_SENTENCE_THRESHOLD
    assert DEFAULT_ISSUE_THRESHOLD <= DEFAULT_SENTENCE_THRESHOLD


def test_one_hit_on_an_unweighted_set_is_a_match(tmp_path):
    path = tmp_path / "one.yaml"
    path.write_text('set_id: one\npatterns:\n'
                    '  - name: only\n    category: LEX\n'
                    '    definition: \'{"frobnicate"}\'\n', encoding="utf-8")
    triager = Triager(pattern_set=load_pattern_set(path))
    assert triager.classify_text("We frobnicate the buffer.", "X").is_match


def test_thresholds_move_the_decision():
    permissive = Triager(issue_threshold=0.1, sentence_threshold=0.1)
    strict = Triager(issue_threshold=100.0, sentence_threshold=100.0)
    assert permissive.classify_text(SLOW, "x").is_match
    assert not strict.classify_text(SLOW, "x").is_match


def test_security_set_routes_a_hardening_report():
    triager = Triager(pattern_set=load_pattern_set("security"))
    verdict = triager.classify_text(
        "Heap buffer overflow in the PNG decoder. CVE-2026-1234. A crash "
        "input from oss-fuzz is attached.", "GHSA-x")
    assert verdict.is_match
    assert {"memory_safety", "advisory_reference"} & set(verdict.patterns)


def test_security_set_ignores_a_feature_request():
    triager = Triager(pattern_set=load_pattern_set("security"))
    assert not triager.classify_text(
        "Add a --verbose flag to the exporter.", "GH-9").is_match


def test_report_describes_the_configuration(triager):
    report = triager.report()
    assert report["n_patterns"] == 80
    assert report["backend"] == "simple"
    assert "n_repaired" in report


# --- ingestion -------------------------------------------------------------

def test_report_text_keeps_the_title_as_its_own_sentence():
    report = Report(identifier="X", title="Parsing is slow", body="Details here.")
    assert report.text.startswith("Parsing is slow.")


def test_csv_column_names_are_matched_loosely(tmp_path):
    path = tmp_path / "issues.csv"
    path.write_text("Key,Summary,Description\nA-1,Slow parse,Takes 30 seconds\n",
                    encoding="utf-8")
    reports = load_reports(path)
    assert len(reports) == 1
    assert reports[0].identifier == "A-1"
    assert "30 seconds" in reports[0].text


def test_csv_without_a_text_column_fails_loudly(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("key,assignee\nA-1,alice\n", encoding="utf-8")
    with pytest.raises(ValueError) as excinfo:
        load_reports(path)
    assert "expected one of" in str(excinfo.value)


def test_osv_advisory_yields_cwe_and_reproducer_hint(tmp_path):
    path = tmp_path / "GHSA-abcd.json"
    path.write_text(json.dumps({
        "schema_version": "1.6.0",
        "id": "GHSA-abcd-1234-efgh",
        "summary": "Heap overflow in decoder",
        "details": "A crafted input overflows the buffer. CWE-122.",
        "affected": [],
        "references": [{"type": "WEB",
                        "url": "https://oss-fuzz.com/testcase?id=1"}],
    }), encoding="utf-8")
    reports = from_osv(path)
    assert len(reports) == 1
    assert reports[0].cwe == "CWE-122"
    assert reports[0].reproducer


def test_osv_reads_a_whole_directory(tmp_path):
    for index in range(3):
        (tmp_path / f"a{index}.json").write_text(json.dumps(
            {"id": f"OSV-{index}", "summary": "x", "affected": [],
             "schema_version": "1.6.0"}), encoding="utf-8")
    assert len(from_osv(tmp_path)) == 3


def test_format_detection(tmp_path):
    csv_path = tmp_path / "a.csv"
    csv_path.write_text("key,summary\n1,x\n", encoding="utf-8")
    osv_path = tmp_path / "b.json"
    osv_path.write_text(json.dumps({"id": "CVE-2026-1", "affected": [],
                                    "schema_version": "1.6.0"}),
                        encoding="utf-8")
    github_path = tmp_path / "c.json"
    github_path.write_text(json.dumps([{"number": 4, "title": "t", "body": "b"}]),
                           encoding="utf-8")
    assert detect_format(csv_path) == "csv"
    assert detect_format(osv_path) == "osv"
    assert detect_format(github_path) == "github"


# --- command line ----------------------------------------------------------

def _corpus(tmp_path):
    path = tmp_path / "issues.csv"
    path.write_text("key,summary,description\n"
                    f"A-1,Slow parse,\"{SLOW}\"\n"
                    f"A-2,Rename flag,\"{BORING}\"\n", encoding="utf-8")
    return path


def test_cli_classify_json(tmp_path, capsys):
    assert main(["classify", str(_corpus(tmp_path)), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "parapet-triage"
    assert len(payload["results"]) == 2
    labels = {item["identifier"]: item["label"] for item in payload["results"]}
    assert labels["A-1"] == "match" and labels["A-2"] == "no-match"


def test_cli_classify_writes_records(tmp_path):
    out = tmp_path / "records"
    assert main(["classify", str(_corpus(tmp_path)), "--record", str(out)]) == 0
    written = sorted(out.glob("*.json"))
    assert [path.stem for path in written] == ["A-1"]     # only matches
    payload = json.loads(written[0].read_text(encoding="utf-8"))
    assert payload["exposure"]["identifier"] == "A-1"
    assert payload["exposure"]["labels"]


def test_cli_fail_on_match_is_a_ci_gate(tmp_path):
    assert main(["classify", str(_corpus(tmp_path)), "--fail-on-match"]) == 2


def test_cli_patterns_lists_the_set(capsys):
    assert main(["patterns", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["set_id"] == "performance-v1"
    assert len(payload["patterns"]) == 80


def test_cli_doctor_runs_without_optional_extras(capsys):
    assert main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert "pattern set performance" in out
    assert "backend simple" in out


def test_cli_explain(tmp_path, capsys):
    assert main(["explain", str(_corpus(tmp_path)), "--id", "A-1"]) == 0
    assert "A-1" in capsys.readouterr().out
