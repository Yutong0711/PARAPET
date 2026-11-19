"""Functional tests for parapet.validate and parapet.extract.

The first group needs no model and no JDK. The ``jvm`` group compiles and runs
the real C1/C2 harness against hand-written patches and needs javac/java.
"""

from __future__ import annotations

import shutil

import pytest

from parapet.case import load_case
from parapet.extract import extract_java
from parapet.validate import claim_level, compare_probes, evaluate_check, parse_result, prepare_support, validate_patch

HAS_JDK = shutil.which("javac") is not None and shutil.which("java") is not None


# ------------------------------------------------------------------ extraction (L1)

def test_extracts_first_fenced_block_declaring_the_class_verbatim():
    body = "package a;\n\npublic final class PrefsCodec {\n  int x; \n}\n"
    text = f"Here you go:\n```java\n{body}```\nand a note\n```java\nclass Other {{}}\n```"
    code, how = extract_java(text, "PrefsCodec")
    assert code == body
    assert "#1" in how


def test_skips_blocks_that_do_not_declare_the_class():
    text = "```\nclass Helper {}\n```\n```java\npublic class PrefsCodec {}\n```\n"
    code, how = extract_java(text, "PrefsCodec")
    assert code == "public class PrefsCodec {}\n" and "#2" in how


def test_whole_response_only_when_there_are_no_fences():
    code, _ = extract_java("package a;\npublic class PrefsCodec {}", "PrefsCodec")
    assert code == "package a;\npublic class PrefsCodec {}\n"
    code, how = extract_java("Sure! public class PrefsCodec {}", "PrefsCodec")
    assert code is None


def test_truncated_or_empty_responses_are_not_parseable():
    assert extract_java("```java\npublic class PrefsCodec {", "PrefsCodec")[0] is None
    assert extract_java("", "PrefsCodec")[0] is None
    assert extract_java(None, "PrefsCodec")[0] is None
    assert extract_java("```java\npublic class PrefsCodecX {}\n```", "PrefsCodec")[0] is None


# ------------------------------------------------------------------ check semantics

def test_parse_result_takes_the_last_result_line():
    out = 'noise\nPARAPET_RESULT {"a":1}\n[Fatal Error] x\nPARAPET_RESULT {"a":2}\n'
    assert parse_result(out) == {"a": 2}
    assert parse_result("nothing here") is None


@pytest.mark.parametrize(
    "result, passed",
    [
        ({"fired": False, "outcome": "rejected"}, True),
        ({"fired": False, "outcome": "accepted"}, True),
        ({"fired": True, "outcome": "rejected"}, False),
        ({"fired": False, "outcome": "harness-error"}, False),
        (None, False),
    ],
)
def test_payload_check_semantics(result, passed):
    assert evaluate_check("reproducer", result)[0] is passed


def test_functional_check_requires_zero_failures_and_some_passes():
    assert evaluate_check("functional", {"passed": 11, "failed": 0, "tests": []})[0]
    assert not evaluate_check("functional", {"passed": 10, "failed": 1, "tests": [{"name": "t", "ok": False}]})[0]
    assert not evaluate_check("functional", {"passed": 0, "failed": 0, "tests": []})[0]


def test_claim_levels():
    ok = {"passed": True}
    bad = {"passed": False}
    assert claim_level(False, {}) == "L1"
    assert claim_level(True, {"reproducer": bad}) == "L2"
    assert claim_level(True, {"reproducer": ok, "heldout1": bad, "heldout2": ok, "functional": ok}) == "L3"
    assert claim_level(True, {"reproducer": ok, "heldout1": ok, "heldout2": ok, "functional": bad}) == "L3"
    assert claim_level(True, {"reproducer": ok, "heldout1": ok, "heldout2": ok, "functional": ok}) == "L4"


def _probes(rows):
    return {"checks": {"probes": {"result": {"probes": rows}}}}


def test_compare_probes_reports_now_rejected_and_changed_results():
    original = _probes([
        {"probe": "a", "status": "accepted", "digest": "1"},
        {"probe": "b", "status": "accepted", "digest": "2"},
        {"probe": "c", "status": "accepted", "digest": "3"},
        {"probe": "d", "status": "rejected", "digest": None},
    ])
    patched = _probes([
        {"probe": "a", "status": "accepted", "digest": "1"},
        {"probe": "b", "status": "rejected", "digest": None, "exception": "E"},
        {"probe": "c", "status": "accepted", "digest": "9"},
        {"probe": "d", "status": "rejected", "digest": None},
    ])
    cmp = compare_probes(original, patched)
    assert cmp["evaluated"]
    assert [x["probe"] for x in cmp["now_rejected"]] == ["b"]
    assert [x["probe"] for x in cmp["different_result"]] == ["c"]


def test_compare_probes_unavailable_is_not_silently_clean():
    cmp = compare_probes(_probes([{"probe": "a", "status": "accepted", "digest": "1"}]), {"checks": {}})
    assert cmp["evaluated"] is False


# ------------------------------------------------------------------ mechanism matching

def test_mechanism_rule_maps_reference_fixes_to_themselves():
    for cid in ("C1", "C2"):
        case = load_case(cid)
        for rid, ref in case.references.items():
            assert case.match_reference(ref.path.read_text()) == rid


# ------------------------------------------------------------------ end to end on the real harness

@pytest.mark.jvm
@pytest.mark.skipif(not HAS_JDK, reason="no JDK on PATH")
@pytest.mark.parametrize("cid", ["C1", "C2"])
def test_harness_separates_vulnerable_control_and_reference(cid, tmp_path):
    case = load_case(cid)
    support, _ = prepare_support(case, tmp_path)
    v0 = validate_patch(case, "V0", "vulnerable", case.read_target(), tmp_path, support, tmp_path / "l" / "V0")
    ctl = validate_patch(case, "CONTROL", "control", case.control_path.read_text(), tmp_path, support,
                         tmp_path / "l" / "C")
    r1 = validate_patch(case, "R1", "reference", case.references["R1"].path.read_text(), tmp_path, support,
                        tmp_path / "l" / "R1")
    # The unpatched source fires every canary but keeps required behavior.
    assert v0["claim_level"] == "L2"
    assert all(v0["checks"][n]["result"]["fired"] for n in ("reproducer", "heldout1", "heldout2"))
    assert v0["checks"]["functional"]["passed"]
    # The incomplete control blocks the reproducer, and the held-out variants catch it.
    assert ctl["checks"]["reproducer"]["passed"]
    assert not ctl["checks"]["heldout1"]["passed"] and not ctl["checks"]["heldout2"]["passed"]
    assert ctl["claim_level"] == "L3" and not ctl["admissible"]
    # A reference fix is admissible.
    assert r1["claim_level"] == "L4" and r1["admissible"]


@pytest.mark.jvm
@pytest.mark.skipif(not HAS_JDK, reason="no JDK on PATH")
def test_a_patch_that_does_not_compile_stops_at_l1(tmp_path):
    case = load_case("C1")
    support, _ = prepare_support(case, tmp_path)
    v = validate_patch(case, "BROKEN", "candidate", "package example.prefs; class PrefsCodec {", tmp_path,
                       support, tmp_path / "l")
    assert v["claim_level"] == "L1" and not v["admissible"]
    assert all(not c["passed"] for c in v["checks"].values())
