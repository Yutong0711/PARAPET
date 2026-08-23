"""Java scanning, DSM construction, and the review-cost verdict."""

import pytest

from parapet_scope import (DEPENDS, DESIGN_LEVEL, EXTENDS, LOCALIZED,
                           analyse, build_diff_dsm, build_dsm, is_test_path,
                           parse_file)
from parapet_scope.classify import classify_scope, detect_cochange, review_order
from parapet_scope.javasrc import strip_comments_and_strings


# --- the scanner -----------------------------------------------------------

def test_package_types_and_imports_are_read(base_sources):
    parsed = parse_file("src/main/java/acme/Loader.java",
                        base_sources["src/main/java/acme/Loader.java"])
    assert parsed.package == "acme"
    assert parsed.types == ["Loader"]
    assert "acme.util.Buffer" in parsed.imports
    assert parsed.qualified_name == "acme.Loader"


def test_braces_in_comments_and_strings_do_not_confuse_the_scanner():
    source = 'class A { /* } */ String s = "} {"; void m() {} }'
    cleaned = strip_comments_and_strings(source)
    assert cleaned.count("{") == cleaned.count("}")


def test_stripping_preserves_offsets():
    source = 'class A {\n  // }\n  String s = "x";\n}\n'
    assert len(strip_comments_and_strings(source)) == len(source)
    assert strip_comments_and_strings(source).count("\n") == source.count("\n")


def test_extends_is_recorded(base_sources):
    parsed = parse_file("src/main/java/acme/FastLoader.java",
                        base_sources["src/main/java/acme/FastLoader.java"])
    assert "Loader" in parsed.extends


def test_test_files_are_recognised_by_path_and_by_name():
    assert is_test_path("src/test/java/acme/LoaderTest.java")
    assert is_test_path("foo/BufferTest.java")
    assert not is_test_path("src/main/java/acme/Loader.java")


# --- the matrix ------------------------------------------------------------

def test_dsm_resolves_an_explicit_import(base_sources):
    dsm = build_dsm(base_sources)
    assert ("src/main/java/acme/Loader.java",
            "src/main/java/acme/util/Buffer.java", DEPENDS) in dsm.edges


def test_dsm_marks_inheritance_as_ext(base_sources):
    dsm = build_dsm(base_sources)
    assert ("src/main/java/acme/FastLoader.java",
            "src/main/java/acme/Loader.java", EXTENDS) in dsm.edges


def test_dsm_resolves_a_same_package_reference(base_sources):
    """Report uses Loader with no import; same package must still resolve."""
    dsm = build_dsm(base_sources)
    assert ("src/main/java/acme/Report.java",
            "src/main/java/acme/Loader.java", DEPENDS) in dsm.edges


def test_dsm_ignores_types_outside_the_repository(base_sources):
    dsm = build_dsm(base_sources)
    targets = {edge[1] for edge in dsm.edges}
    assert not any("junit" in target.lower() for target in targets)


def test_dsm_has_no_self_edges(base_sources):
    dsm = build_dsm(base_sources)
    assert all(edge[0] != edge[1] for edge in dsm.edges)


def test_dsm_render_is_readable(base_sources):
    text = build_dsm(base_sources).render()
    assert "Loader" in text and "(1)" in text


# --- scope classification --------------------------------------------------

def test_one_file_no_structure_change_is_localized(base_sources, single_file_edit):
    diff = build_diff_dsm(base_sources, single_file_edit,
                          ["src/main/java/acme/util/Buffer.java"], "abc123")
    assert classify_scope(diff) == LOCALIZED
    assert not diff.added_files


def test_a_new_file_makes_it_design_level(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java",
               "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    assert classify_scope(diff) == DESIGN_LEVEL
    assert diff.added_files == ("src/main/java/acme/Cache.java",)


def test_type_i_change_propagation_is_named(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java",
               "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    verdict = analyse(diff, base_sources, cache_added)
    assert verdict.design_pattern == "Change Propagation (Type-I)"
    assert "adopted by" in verdict.pattern_reason


def test_type_ii_is_rewiring_with_no_new_file(base_sources, rewired):
    changed = ["src/main/java/acme/Loader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, rewired, changed, "ghi789")
    verdict = analyse(diff, base_sources, rewired)
    assert verdict.scope == DESIGN_LEVEL
    assert verdict.design_pattern == "Change Propagation (Type-II)"
    assert not diff.added_files


def test_review_order_puts_the_new_file_first(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java",
               "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    order = review_order(diff)
    assert order[0] == "src/main/java/acme/Cache.java"


def test_advice_is_a_paragraph_a_reviewer_can_act_on(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java", "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    text = analyse(diff, base_sources, cache_added).advice()
    assert "design-level" in text and "review in this order" in text


def test_a_design_level_change_with_no_tests_is_flagged(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java", "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    verdict = analyse(diff, base_sources, cache_added)
    assert any("no test revision" in note for note in verdict.notes)


# --- test/production co-change --------------------------------------------

def test_no_test_change_yields_no_pattern(base_sources, single_file_edit):
    diff = build_diff_dsm(base_sources, single_file_edit,
                          ["src/main/java/acme/util/Buffer.java"], "abc123")
    assert detect_cochange(diff, base_sources, single_file_edit) == []


def test_a_new_test_file_is_test_file_addition(base_sources):
    after = dict(base_sources)
    after["src/test/java/acme/CacheTest.java"] = (
        "package acme;\nimport org.junit.Test;\n"
        "public class CacheTest { @Test public void t() {} }\n")
    diff = build_diff_dsm(base_sources, after,
                          ["src/test/java/acme/CacheTest.java"], "x")
    assert "Test File Addition" in detect_cochange(diff, base_sources, after)


def test_an_added_test_method_is_test_case_addition(base_sources):
    after = dict(base_sources)
    after["src/test/java/acme/LoaderTest.java"] = (
        base_sources["src/test/java/acme/LoaderTest.java"].replace(
            "}\n", "    @Test\n    public void loadsTwo() { }\n}\n", 1))
    diff = build_diff_dsm(base_sources, after,
                          ["src/test/java/acme/LoaderTest.java"], "x")
    assert "Test Case Addition" in detect_cochange(diff, base_sources, after)


def test_verdict_serialises(base_sources, cache_added):
    changed = ["src/main/java/acme/Cache.java", "src/main/java/acme/Loader.java",
               "src/main/java/acme/FastLoader.java",
               "src/main/java/acme/Report.java"]
    diff = build_diff_dsm(base_sources, cache_added, changed, "def456")
    payload = analyse(diff, base_sources, cache_added).to_dict()
    assert payload["scope"] == DESIGN_LEVEL
    assert payload["design_pattern"] == "Change Propagation (Type-I)"
    assert payload["added_files"] == ["src/main/java/acme/Cache.java"]


def test_diff_dsm_serialises(base_sources, cache_added):
    diff = build_diff_dsm(base_sources, cache_added,
                          ["src/main/java/acme/Cache.java"], "def456")
    payload = diff.to_dict()
    assert payload["change_ref"] == "def456"
    assert payload["added_files"] == ["src/main/java/acme/Cache.java"]
