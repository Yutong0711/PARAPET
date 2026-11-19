"""Prompt contents and the hosted-generator refusal (no model, no network)."""

from __future__ import annotations

import pytest

from parapet.case import load_case
from parapet.generate import HostedGeneratorRefused, assert_allowed, is_local, load_generation_settings
from parapet.prompt import build_prompt, prompt_record


@pytest.mark.parametrize("cid", ["C1", "C2"])
def test_prompt_contains_only_the_source_and_the_weakness_class(cid):
    case = load_case(cid)
    prompt = build_prompt(case)
    assert case.cwe_id in prompt and case.cwe_name in prompt
    assert case.read_target().rstrip("\n") in prompt
    # Nothing from the reference fixes, the control patch, or the harness.
    secret_texts = [r.path.read_text() for r in case.references.values()] + [case.control_path.read_text()]
    original_lines = {line.strip() for line in case.read_target().splitlines()}
    for text in secret_texts:
        # Lines a patch adds that carry content (not just braces or comment openers).
        added = [line.strip() for line in text.splitlines()
                 if line.strip() not in original_lines and len(line.strip()) >= 8
                 and any(ch.isalnum() for ch in line)]
        assert added, "reference must differ from the source"
        for line in added:
            assert line not in prompt, f"prompt leaks patch line: {line}"
    for marker in ("GadgetA", "GadgetB", "GadgetC", "PARAPET-CANARY", "HeldOut", "ext.dtd", "PUBLIC"):
        assert marker not in prompt


def test_prompt_hash_is_stable():
    case = load_case("C1")
    assert prompt_record(case)["prompt_sha256"] == prompt_record(case)["prompt_sha256"]


def test_default_generator_is_local_and_hosted_is_refused():
    s = load_generation_settings()
    assert is_local(s["default_generator"]["base_url"])
    assert_allowed(s["default_generator"]["base_url"], allow_hosted_control=False)
    with pytest.raises(HostedGeneratorRefused):
        assert_allowed("https://api.openai.com/v1", allow_hosted_control=False)
    assert_allowed("https://api.openai.com/v1", allow_hosted_control=True)
    assert s["k"] == 5 and len(s["seeds"]) == 5


def test_library_case_prompt_reads_only_the_target_file():
    """L1 needs pinned dependency jars (fetch_jars.sh); skipped where they are absent, e.g. in CI."""
    from parapet.case import CaseError

    try:
        case = load_case("L1")
    except CaseError as e:
        pytest.skip(f"L1 not available here: {e}")
    prompt = build_prompt(case)
    assert case.read_target().rstrip("\n") in prompt
    assert "CWE-611" in prompt
    # The upstream fix's new method and the other library files are not in the prompt.
    assert "enableOrDisableExternalEntityParsing" not in prompt
    assert "public class XMLBuilder2" not in prompt
    for marker in ("PARAPET-CANARY", "ext.dtd", "PUBLIC", "disallow-doctype-decl"):
        assert marker not in prompt
