"""Call graphs, profiles, and where the added cost landed."""

import json

import pytest

from parapet_attrib import (CallGraph, Profile, attribute, build_space, compare,
                            load_graph, load_profile, save_graph)
from parapet_attrib.attribute import detect_patterns, hotspots
from parapet_attrib.javacalls import build_call_graph
from parapet_attrib.profiles import MethodProfile


# --- the graph -------------------------------------------------------------

@pytest.fixture
def chain():
    """A -> B -> C -> D, plus E calling B."""
    return CallGraph.from_edges([("A", "B"), ("B", "C"), ("C", "D"), ("E", "B")])


def test_space_layers_by_distance(chain):
    space = build_space(chain, "B")
    assert space.upper_layers == (("A", "E"),)
    assert space.lower_layers == (("C",), ("D",))
    assert space.layer_of("D") == ("callee", 2)
    assert space.layer_of("A") == ("caller", 1)


def test_space_contains_the_seed(chain):
    assert "B" in build_space(chain, "B").methods


def test_self_calls_do_not_appear_in_a_space():
    graph = CallGraph.from_edges([("A", "A"), ("A", "B")])
    assert build_space(graph, "A").callees == ("B",)


def test_cycles_terminate():
    graph = CallGraph.from_edges([("A", "B"), ("B", "C"), ("C", "A")])
    assert build_space(graph, "A").methods == {"A", "B", "C"}


def test_max_layers_bounds_the_space(chain):
    assert build_space(chain, "B", max_layers=1).callees == ("C",)


def test_unknown_seed_raises(chain):
    with pytest.raises(KeyError):
        build_space(chain, "Z")


# --- importers -------------------------------------------------------------

def test_java_callgraph_import_normalises_names(tmp_path):
    path = tmp_path / "raw.txt"
    path.write_text("C:a.Foo b.Bar\nM:a.Foo:bar (M)b.Baz:qux\n", encoding="utf-8")
    graph = load_graph(path)
    assert graph.callees("a.Foo#bar") == {"b.Baz#qux"}


def test_csv_import(tmp_path):
    path = tmp_path / "g.csv"
    path.write_text("caller,callee\nA#x,B#y\nB#y,\n", encoding="utf-8")
    graph = load_graph(path)
    assert graph.callees("A#x") == {"B#y"}
    assert "B#y" in graph


def test_json_roundtrip(tmp_path, chain):
    path = tmp_path / "g.json"
    save_graph(chain, path)
    restored = load_graph(path)
    assert restored.methods == chain.methods
    assert restored.n_edges == chain.n_edges


# --- java source -----------------------------------------------------------

JAVA = {
    "acme/Loader.java": """
package acme;
public class Loader {
    private Cache cache;
    public byte[] load(String name) {
        return cache.get(name);
    }
    public byte[] loadAll() {
        return load("a");
    }
}
""",
    "acme/Cache.java": """
package acme;
public class Cache {
    public byte[] get(String key) {
        return fetch(key);
    }
    private byte[] fetch(String key) { return new byte[0]; }
}
""",
}


def test_call_graph_from_java_source():
    graph = build_call_graph(JAVA)
    assert "acme.Loader#load" in graph.methods
    assert ("acme.Loader#load", "acme.Cache#get") in graph.edges


def test_a_call_within_the_same_type_resolves():
    graph = build_call_graph(JAVA)
    assert ("acme.Cache#get", "acme.Cache#fetch") in graph.edges
    assert ("acme.Loader#loadAll", "acme.Loader#load") in graph.edges


def test_control_flow_is_not_a_call():
    graph = build_call_graph({"a/A.java": """
package a;
public class A {
    public void m() {
        if (true) { while (false) { } }
        for (int i = 0; i < 3; i++) { }
    }
}
"""})
    assert not any(callee.endswith(("#if", "#for", "#while"))
                   for _caller, callee in graph.edges)


# --- profiles --------------------------------------------------------------

def _profile(label, values, unit="ms"):
    profile = Profile(label=label, unit=unit)
    for method, (time, own, count) in values.items():
        profile.methods[method] = MethodProfile(method, time, own, count)
    return profile


def test_derived_metrics():
    record = MethodProfile("A", time=10.0, own_time=2.0, count=100)
    assert record.callee_time == pytest.approx(8.0)
    assert record.own_share == pytest.approx(0.2)
    assert record.time_per_call == pytest.approx(0.1)
    assert MethodProfile("B").own_share is None


def test_compare_reports_direction_and_size():
    before = _profile("b", {"A": (10.0, 10.0, 5)})
    after = _profile("a", {"A": (12.0, 12.0, 5)})
    delta = compare(before, after)[0]
    assert delta.status == "slower"
    assert delta.absolute == pytest.approx(2.0)
    assert delta.relative == pytest.approx(0.2)


def test_noise_floor_drops_tiny_changes():
    before = _profile("b", {"A": (100.0, 100.0, 1)})
    after = _profile("a", {"A": (100.3, 100.3, 1)})
    assert compare(before, after, noise_floor=0.01) == []
    assert compare(before, after, noise_floor=0.0)


def test_a_method_that_appeared_is_labelled():
    before = _profile("b", {"A": (1.0, 1.0, 1)})
    after = _profile("a", {"A": (1.0, 1.0, 1), "B": (5.0, 5.0, 1)})
    statuses = {d.method: d.status for d in compare(before, after, noise_floor=0.0)}
    assert statuses["B"] == "appeared"


def test_csv_profile_import(tmp_path):
    path = tmp_path / "p.csv"
    path.write_text("method,time,own_time,count\nA#x,10,4,100\n", encoding="utf-8")
    profile = load_profile(path)
    assert profile.value("A#x") == 10.0
    assert profile.get("A#x").own_share == pytest.approx(0.4)


def test_jmh_profile_import(tmp_path):
    path = tmp_path / "jmh.json"
    path.write_text(json.dumps([{
        "benchmark": "acme.LoadBench.load",
        "primaryMetric": {"score": 42.0, "scoreUnit": "ops/s"},
        "measurementIterations": 5}]), encoding="utf-8")
    profile = load_profile(path)
    assert profile.value("acme.LoadBench#load") == 42.0
    assert profile.unit == "ops/s"


# --- attribution -----------------------------------------------------------

def test_cost_in_the_changed_method_is_attributed_here(chain):
    before = _profile("b", {"A": (10, 2, 1), "B": (8, 4, 1), "C": (4, 4, 1)})
    after = _profile("a", {"A": (14, 2, 1), "B": (12, 8, 1), "C": (4, 4, 1)})
    result = attribute(chain, before, after, ["B"])
    assert result.where() == "here"
    assert result.in_changed_methods > 0


def test_cost_below_the_changed_method_is_attributed_below(chain):
    before = _profile("b", {"A": (10, 2, 1), "B": (8, 1, 1), "C": (7, 3, 1),
                            "D": (4, 4, 1)})
    after = _profile("a", {"A": (16, 2, 1), "B": (14, 1, 1), "C": (13, 3, 1),
                           "D": (10, 10, 1)})
    result = attribute(chain, before, after, ["B"])
    assert result.in_callees > result.in_changed_methods


def test_cost_outside_the_space_is_flagged():
    graph = CallGraph.from_edges([("A", "B"), ("X", "Y")])
    before = _profile("b", {"A": (1, 1, 1), "B": (1, 1, 1), "X": (1, 1, 1),
                            "Y": (1, 1, 1)})
    after = _profile("a", {"A": (1, 1, 1), "B": (1, 1, 1), "X": (10, 10, 1),
                           "Y": (10, 10, 1)})
    result = attribute(graph, before, after, ["A"])
    assert result.where() == "elsewhere"
    assert any("outside the space" in w for w in result.warnings)


def test_a_changed_method_missing_from_the_graph_is_reported(chain):
    before = _profile("b", {"A": (1, 1, 1)})
    after = _profile("a", {"A": (2, 2, 1)})
    result = attribute(chain, before, after, ["B", "NotInGraph"])
    assert any("not in the call graph" in w for w in result.warnings)


def test_summary_names_where_the_cost_went(chain):
    before = _profile("b", {"A": (10, 2, 1), "B": (8, 4, 1)})
    after = _profile("a", {"A": (14, 2, 1), "B": (12, 8, 1)})
    text = attribute(chain, before, after, ["B"], change_ref="abc123").summary()
    assert "abc123" in text
    assert "the added cost landed" in text


def test_attribution_serialises(chain):
    before = _profile("b", {"A": (10, 2, 1), "B": (8, 4, 1)})
    after = _profile("a", {"A": (14, 2, 1), "B": (12, 8, 1)})
    payload = attribute(chain, before, after, ["B"]).to_dict()
    assert payload["where"] in ("here", "below", "above", "elsewhere")
    assert payload["changed_methods"] == ["B"]


# --- the two patterns ------------------------------------------------------

def test_expensive_callee_is_named(chain):
    """B's own time is a sliver of its total, and C got slower."""
    before = _profile("b", {"B": (10, 1, 1), "C": (9, 9, 1)})
    after = _profile("a", {"B": (20, 1, 1), "C": (19, 19, 1)})
    found = detect_patterns(chain, before, after, {"B", "C"})
    assert any(item["pattern"] == "Expensive Callee" and item["method"] == "B"
               for item in found)


def test_inefficient_caller_is_named(chain):
    """D is cheap per call and unchanged, but is called far more often."""
    before = _profile("b", {"D": (10, 10, 1000)})
    after = _profile("a", {"D": (30, 30, 3000)})
    found = detect_patterns(chain, before, after, {"D"})
    assert any(item["pattern"] == "Inefficient Caller" for item in found)


def test_a_faster_method_produces_no_pattern(chain):
    before = _profile("b", {"B": (20, 2, 1)})
    after = _profile("a", {"B": (10, 1, 1)})
    assert detect_patterns(chain, before, after, {"B"}) == []


def test_hotspots_stay_inside_the_space(chain):
    profile = _profile("p", {"A": (5, 5, 1), "B": (9, 9, 1), "C": (7, 7, 1),
                             "D": (3, 3, 1)})
    rows = hotspots(profile, chain, ["C"], limit=5)
    assert rows[0]["method"] == "B"        # C's caller chain reaches B
    assert all(row["method"] in build_space(chain, "C").methods for row in rows)
