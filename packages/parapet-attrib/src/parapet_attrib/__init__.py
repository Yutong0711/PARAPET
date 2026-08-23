"""parapet-attrib: where in the architecture did the added cost land.

A benchmark tells you a change cost 4%. It does not tell you whether the
4% is in the method you edited, in something that method calls, or spread
across the callers that reach it, and those three answers call for three
different fixes.

    from parapet_attrib import attribute, load_graph, load_profile

    graph = load_graph("callgraph.csv")
    result = attribute(graph,
                       load_profile("before.csv"),
                       load_profile("after.csv"),
                       changed_methods=["acme.Loader#load"])
    print(result.summary())

Call graphs can be built from Java source with no build, or imported from
java-callgraph, Understand, or any two-column CSV. Profiles can be read
from CSV, JSON, JFR text output, or JMH's JSON.
"""

from .attribute import (Attribution, attribute, detect_patterns, hotspots)
from .graphio import load_graph, save_graph
from .profiles import (Delta, MethodProfile, Profile, compare, load_profile,
                       total_delta)
from .space import CallGraph, Space, build_space, build_spaces, union_space

__all__ = [
    "attribute", "Attribution", "detect_patterns", "hotspots",
    "CallGraph", "Space", "build_space", "build_spaces", "union_space",
    "Profile", "MethodProfile", "Delta", "compare", "total_delta",
    "load_profile", "load_graph", "save_graph",
]
__version__ = "0.1.0"
