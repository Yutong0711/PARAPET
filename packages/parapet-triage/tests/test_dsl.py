"""The pattern language, checked against the definitions it must parse."""

import pytest

from parapet_triage.dsl import (Ordered, Phrases, compile_pattern, compile_set,
                                parse_definition)
from parapet_triage.patterns import load_pattern_set
from parapet_triage.text import get_backend


@pytest.fixture(scope="module")
def backend():
    return get_backend("simple")


def match(backend, definition: str, text: str) -> bool:
    pattern = compile_pattern({"name": "t", "category": "LEX",
                               "definition": definition})
    return pattern.matches(backend.annotate(text))


# --- the grammar -----------------------------------------------------------

def test_phrase_alternation(backend):
    definition = '{"efficient" | "inefficient"}'
    assert match(backend, definition, "this is inefficient")
    assert not match(backend, definition, "this is fine")


def test_phrases_match_on_word_boundaries(backend):
    """'reduce' must not fire on 'irreducible'."""
    assert not match(backend, '{"reduce"}', "the problem is irreducible")
    assert match(backend, '{"reduce"}', "we reduce the buffer")


def test_multi_word_phrase_tolerates_extra_whitespace(backend):
    assert match(backend, '{"speed up"}', "we want to speed\n   up the loop")


def test_plus_is_conjunction(backend):
    definition = '{"memory"} + {"usage"}'
    assert match(backend, definition, "memory usage is high")
    assert not match(backend, definition, "memory is fine")
    # Order does not matter for a conjunction.
    assert match(backend, definition, "usage of memory is high")


def test_semicolon_and_numbering_start_new_clauses(backend):
    definition = '1. {"alpha"}; 2. {"beta"}'
    assert match(backend, definition, "alpha only")
    assert match(backend, definition, "beta only")


def test_numbered_clause_without_a_semicolon(backend):
    """The published 'speed' definition runs 4. ... 5. ... with no separator."""
    definition = '4. {"quick"} 5. word_contains_"slow"'
    assert match(backend, definition, "this is quick")
    assert match(backend, definition, "the slowdown is bad")


def test_top_level_pipe_is_disjunction(backend):
    """'{"byte"} | word_contains{"-byte"}' is an OR, not a conjunction."""
    definition = '{"byte" | "bytes"} | word_contains{"-byte"}'
    assert match(backend, definition, "reads a byte at a time")
    assert match(backend, definition, "a 64-byte header")
    assert not match(backend, definition, "reads a record")


def test_pipe_inside_braces_stays_alternation(backend):
    definition = '{"a" | "b"} + {"c"}'
    assert match(backend, definition, "a and c")
    assert not match(backend, definition, "a and d")


def test_word_contains_matches_inside_a_token(backend):
    assert match(backend, 'word_contains{"accelerat"}', "hardware acceleration")
    assert match(backend, 'word_contains_"prefetch"', "the prefetcher stalls")


def test_text_contains_ignores_word_boundaries(backend):
    assert match(backend, 'text_contains{"../"}', "path is ../etc/passwd")


def test_function_alternation_run_is_not_split(backend):
    """'word_contains_"kb" | "mb"' lists arguments; it is one term."""
    definition = 'word_contains_"kb" | "mb" | "gb"'
    assert match(backend, definition, "the file is 40kb")
    assert match(backend, definition, "uses 12gb")


def test_ner_falls_back_to_surface_cues_without_a_tagger(backend):
    assert match(backend, 'ner_contains_"PERCENT"', "latency rose by 25 percent")
    assert match(backend, 'ner_contains_"PERCENT"', "a 25% regression")
    assert match(backend, 'ner_contains_"DURATION"', "the call takes 300 milliseconds")


def test_token_types(backend):
    assert match(backend, "NUMBER", "there are 12 threads")
    assert not match(backend, "NUMBER", "there are threads")
    assert match(backend, "DURATION", "ran for 4 minutes")


def test_ordering_term(backend):
    definition = '"one" is before "per"'
    assert match(backend, definition, "one request per second")
    assert not match(backend, definition, "per second one request")


def test_repeated_noun_builtin(backend):
    definition = "two nouns are the same"
    assert match(backend, definition, "we copy it byte by byte")
    assert not match(backend, definition, "the file was written by the daemon")


def test_per_noun_per_noun_builtin(backend):
    assert match(backend, "per_NN_per_NN", "cost is per request per node")
    assert not match(backend, "per_NN_per_NN", "cost is per request")


# --- robustness ------------------------------------------------------------

def test_missing_opening_quote_is_repaired():
    """The published 'memory' definition drops one opening quote."""
    definition = '{"memory"} + {"consume" | consumption" | "leak"}'
    pattern = compile_pattern({"name": "memory", "category": "STR",
                               "definition": definition})
    assert any("opening quotation" in repair for repair in pattern.repairs)
    phrases = [term for clause in pattern.clauses for term in clause.terms
               if isinstance(term, Phrases)]
    joined = {phrase for term in phrases for phrase in term.phrases}
    assert "consumption" in joined


def test_missing_closing_quote_is_repaired():
    definition = '{"cost" | "costs}'
    pattern = compile_pattern({"name": "cost", "category": "STR",
                               "definition": definition})
    assert pattern.repairs
    assert pattern.usable


def test_empty_definition_never_fires(backend):
    pattern = compile_pattern({"name": "x", "category": "LEX", "definition": ""})
    assert not pattern.usable
    assert not pattern.matches(backend.annotate("anything at all"))


# --- the shipped sets ------------------------------------------------------

def test_performance_set_compiles_completely():
    pattern_set = load_pattern_set("performance")
    compiled, report = compile_set(pattern_set.patterns)
    assert len(compiled) == 80
    assert report["n_usable"] == 80, report["unusable"]
    # The published set has known malformed cells; the count is pinned so a
    # future edit that introduces a new one is noticed.
    assert report["n_repaired"] <= 8


def test_performance_set_category_split_matches_the_publication():
    counts = load_pattern_set("performance").categories()
    assert counts == {"LEX": 37, "STR": 30, "SEM": 7, "PRF": 6}


def test_security_set_compiles_completely():
    pattern_set = load_pattern_set("security")
    compiled, report = compile_set(pattern_set.patterns)
    assert report["n_usable"] == len(compiled)
    assert report["n_repaired"] == 0


def test_unknown_pattern_set_names_the_builtins():
    with pytest.raises(FileNotFoundError) as excinfo:
        load_pattern_set("does-not-exist")
    assert "performance" in str(excinfo.value)
