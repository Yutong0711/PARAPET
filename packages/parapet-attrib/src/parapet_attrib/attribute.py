"""Where in the architecture the added cost landed.

A benchmark says a change made something 4% slower. That is a number, not
an answer. The answer a maintainer needs is *where*: in the method that
changed, in something it calls, or spread across the callers that reach
it. Those three cases call for three different responses, and only the
first is fixed by editing the diff.

This module takes the changed methods, the call graph, and profiles from
before and after, and answers that question. It also names the two shapes
that recur:

``Expensive Callee``
    the cost is below the changed method. Its own time barely moved; what
    it calls got slower. Fix the callee, not the caller.
``Inefficient Caller``
    the method itself is cheap per call and did not change, but something
    calls it far more often than before. Fix the call site.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .profiles import Delta, Profile, compare
from .space import CallGraph, Space, build_spaces, union_space

# Own time at or below this share of total means the cost is below, not here.
EXPENSIVE_CALLEE_OWN_SHARE = 0.35
# Own time at or above this share means there is nothing below to blame.
INEFFICIENT_CALLER_OWN_SHARE = 0.80
# A call count that grew by at least this much is a change in call pattern,
# not measurement noise.
COUNT_GROWTH = 0.25


@dataclass
class Attribution:
    """Where the added cost of one change went."""

    change_ref: str = ""
    metric: str = "time"
    total_before: float = 0.0
    total_after: float = 0.0
    changed_methods: List[str] = field(default_factory=list)
    space_size: int = 0
    graph_size: int = 0
    inside_space: float = 0.0
    outside_space: float = 0.0
    in_changed_methods: float = 0.0
    in_callees: float = 0.0
    in_callers: float = 0.0
    top_contributors: List[dict] = field(default_factory=list)
    patterns: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_delta(self) -> float:
        return self.total_after - self.total_before

    @property
    def relative_delta(self) -> Optional[float]:
        if not self.total_before:
            return None
        return self.total_delta / self.total_before

    @property
    def contained(self) -> Optional[float]:
        """The share of the added cost that fell inside the space.

        A value near 1 means the change explains its own cost. A low value
        means something else moved at the same time, and the measurement
        should be repeated before the number is trusted.
        """
        added = self.inside_space + self.outside_space
        return self.inside_space / added if added > 0 else None

    def where(self) -> str:
        """The one-word answer: here, below, above, or elsewhere."""
        inside = self.in_changed_methods + self.in_callees + self.in_callers
        if inside <= 0:
            return "elsewhere"
        parts = {"here": self.in_changed_methods, "below": self.in_callees,
                 "above": self.in_callers}
        return max(parts, key=parts.get)

    def summary(self) -> str:
        relative = self.relative_delta
        head = (f"{self.change_ref or 'change'}: total {self.metric} "
                f"{self.total_before:.4g} -> {self.total_after:.4g}")
        if relative is not None:
            head += f" ({relative:+.1%})"
        lines = [head]
        where = self.where()
        explain = {"here": "in the methods that changed",
                   "below": "in what those methods call",
                   "above": "in the methods that call them",
                   "elsewhere": "outside the space of the change"}[where]
        lines.append(f"  the added cost landed {explain}")
        lines.append(f"  in changed methods {self.in_changed_methods:+.4g}, "
                     f"below {self.in_callees:+.4g}, "
                     f"above {self.in_callers:+.4g}, "
                     f"outside {self.outside_space:+.4g}")
        contained = self.contained
        if contained is not None:
            lines.append(f"  {contained:.0%} of the increase is inside the "
                         f"space of {self.space_size} method(s) "
                         f"({self.space_size / max(1, self.graph_size):.0%} "
                         "of the system)")
        for item in self.top_contributors[:5]:
            lines.append(f"    {item['role']:<8} {_short(item['method']):<44} "
                         f"{item['absolute']:+.4g}")
        for pattern in self.patterns[:3]:
            lines.append(f"  pattern: {pattern['pattern']} - {pattern['reason']}")
        for warning in self.warnings:
            lines.append(f"  warning: {warning}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"change_ref": self.change_ref, "metric": self.metric,
                "total_before": self.total_before, "total_after": self.total_after,
                "total_delta": round(self.total_delta, 6),
                "relative_delta": (None if self.relative_delta is None
                                   else round(self.relative_delta, 6)),
                "where": self.where(),
                "contained": None if self.contained is None else round(self.contained, 4),
                "changed_methods": list(self.changed_methods),
                "space_size": self.space_size, "graph_size": self.graph_size,
                "in_changed_methods": round(self.in_changed_methods, 6),
                "in_callees": round(self.in_callees, 6),
                "in_callers": round(self.in_callers, 6),
                "outside_space": round(self.outside_space, 6),
                "top_contributors": list(self.top_contributors),
                "patterns": list(self.patterns),
                "warnings": list(self.warnings)}


def _short(method: str) -> str:
    owner, _, name = method.partition("#")
    return f"{owner.rsplit('.', 1)[-1]}#{name}" if name else method


def attribute(graph: CallGraph,
              before: Profile,
              after: Profile,
              changed_methods: Sequence[str],
              metric: str = "time",
              max_layers: int = 0,
              noise_floor: float = 0.01,
              change_ref: str = "") -> Attribution:
    """Split the measured change in cost across the regions of the graph.

    Only increases are attributed. A method that got faster is reported in
    ``top_contributors`` with a negative number, but the shares below
    answer "where did the *added* cost go", and mixing a saving into that
    denominator would understate the regression.
    """
    known = [method for method in changed_methods if method in graph]
    missing = [method for method in changed_methods if method not in graph]

    spaces = build_spaces(graph, known, max_layers)
    space_methods = union_space(spaces.values())
    changed_set = set(known)
    callee_set: Set[str] = set()
    caller_set: Set[str] = set()
    for space in spaces.values():
        callee_set |= set(space.callees)
        caller_set |= set(space.callers)
    callee_set -= changed_set
    caller_set -= changed_set | callee_set

    result = Attribution(change_ref=change_ref, metric=metric,
                         total_before=before.total(metric),
                         total_after=after.total(metric),
                         changed_methods=list(known),
                         space_size=len(space_methods),
                         graph_size=len(graph))

    for method in missing:
        result.warnings.append(
            f"{method} changed but is not in the call graph; its cost cannot "
            "be attributed")

    deltas = compare(before, after, metric, noise_floor)
    contributors = []
    for delta in deltas:
        added = delta.absolute
        if added is None or added <= 0:
            if added is not None and added < 0:
                contributors.append({"method": delta.method,
                                     "role": _role(delta.method, changed_set,
                                                   callee_set, caller_set),
                                     "absolute": round(added, 6),
                                     "relative": delta.relative,
                                     "status": delta.status})
            continue
        role = _role(delta.method, changed_set, callee_set, caller_set)
        if role == "changed":
            result.in_changed_methods += added
        elif role == "callee":
            result.in_callees += added
        elif role == "caller":
            result.in_callers += added
        else:
            result.outside_space += added
        if role != "outside":
            result.inside_space += added
        contributors.append({"method": delta.method, "role": role,
                             "absolute": round(added, 6),
                             "relative": delta.relative, "status": delta.status})

    result.top_contributors = sorted(
        contributors, key=lambda item: -abs(item["absolute"]))[:20]
    result.patterns = detect_patterns(graph, before, after, space_methods, metric)

    if not known:
        result.warnings.append(
            "none of the changed methods are in the call graph; nothing was "
            "attributed")
    contained = result.contained
    if contained is not None and contained < 0.5:
        result.warnings.append(
            f"{1 - contained:.0%} of the increase landed outside the space of "
            "the change; something else moved during the measurement, so "
            "repeat it before acting on this")
    return result


def _role(method: str, changed: Set[str], callees: Set[str],
          callers: Set[str]) -> str:
    if method in changed:
        return "changed"
    if method in callees:
        return "callee"
    if method in callers:
        return "caller"
    return "outside"


def detect_patterns(graph: CallGraph, before: Profile, after: Profile,
                    scope: Iterable[str], metric: str = "time") -> List[dict]:
    """Name the two shapes, on the methods that got slower."""
    found: List[dict] = []
    for method in sorted(scope):
        record = after.get(method)
        if record is None or record.time is None:
            continue
        old = before.get(method)
        delta = (record.get(metric) or 0.0) - ((old.get(metric) if old else 0.0) or 0.0)
        if delta <= 0:
            continue

        own_share = record.own_share
        if own_share is not None and own_share <= EXPENSIVE_CALLEE_OWN_SHARE:
            culprits = _slower_callees(graph, before, after, method, metric)
            if culprits:
                found.append({
                    "pattern": "Expensive Callee", "method": method,
                    "reason": (f"{_short(method)} spends "
                               f"{1 - own_share:.0%} of its time below it, and "
                               f"{', '.join(_short(c) for c in culprits[:3])} "
                               "got slower"),
                    "culprits": culprits[:5]})
                continue

        if own_share is not None and own_share >= INEFFICIENT_CALLER_OWN_SHARE:
            growth = _count_growth(before, after, method)
            if growth is not None and growth >= COUNT_GROWTH:
                drivers = sorted(graph.callers(method))
                found.append({
                    "pattern": "Inefficient Caller", "method": method,
                    "reason": (f"{_short(method)} did not get slower per call, "
                               f"but is called {growth:+.0%} more often; the "
                               "change is in its callers"),
                    "callers": drivers[:5]})
    return found


def _slower_callees(graph: CallGraph, before: Profile, after: Profile,
                    method: str, metric: str) -> List[str]:
    out = []
    for callee in sorted(graph.callees(method)):
        old = before.value(callee, metric)
        new = after.value(callee, metric)
        if old is not None and new is not None and new > old:
            out.append(callee)
    return out


def _count_growth(before: Profile, after: Profile, method: str) -> Optional[float]:
    old = before.value(method, "count")
    new = after.value(method, "count")
    if not old or new is None:
        return None
    return (new - old) / old


def hotspots(profile: Profile, graph: CallGraph, changed_methods: Sequence[str],
             metric: str = "time", limit: int = 10) -> List[dict]:
    """The most expensive methods inside the space of the change.

    Useful without a second profile: it says what the change is sitting
    next to, which is where a cost increase would show up if one appeared.
    """
    spaces = build_spaces(graph, [m for m in changed_methods if m in graph])
    scope = union_space(spaces.values())
    scored = []
    for method in scope:
        value = profile.value(method, metric)
        if value is not None:
            scored.append({"method": method, metric: value})
    return sorted(scored, key=lambda item: -item[metric])[:limit]
