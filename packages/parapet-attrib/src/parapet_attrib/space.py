"""The region of the architecture a method's cost can reach.

Around any method there are two sets that matter for performance: the
methods that call it, directly or transitively, and the methods it calls.
The first is where its cost shows up; the second is where its cost comes
from. Together with the method itself they form its *space*, and both
halves are laid out in layers by distance.

The point is not the graph. The point is that when a change makes
something slower, the slowdown is almost never confined to the method that
changed, and the space is the smallest region that is guaranteed to
contain it.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass
class CallGraph:
    """Methods and calls, with the two directions indexed."""

    _callees: Dict[str, Set[str]] = field(default_factory=dict)
    _callers: Dict[str, Set[str]] = field(default_factory=dict)

    def add_method(self, method: str) -> None:
        self._callees.setdefault(method, set())
        self._callers.setdefault(method, set())

    def add_call(self, caller: str, callee: str) -> None:
        self.add_method(caller)
        self.add_method(callee)
        if caller != callee:      # direct recursion adds no reachability
            self._callees[caller].add(callee)
            self._callers[callee].add(caller)

    @classmethod
    def from_edges(cls, edges: Iterable[Tuple[str, str]],
                   methods: Optional[Iterable[str]] = None) -> "CallGraph":
        graph = cls()
        for method in methods or ():
            graph.add_method(method)
        for caller, callee in edges:
            graph.add_call(caller, callee)
        return graph

    @property
    def methods(self) -> Tuple[str, ...]:
        return tuple(sorted(self._callees))

    def __len__(self) -> int:
        return len(self._callees)

    def __contains__(self, method: str) -> bool:
        return method in self._callees

    @property
    def n_edges(self) -> int:
        return sum(len(targets) for targets in self._callees.values())

    def callees(self, method: str) -> Set[str]:
        return self._callees.get(method, set())

    def callers(self, method: str) -> Set[str]:
        return self._callers.get(method, set())

    def _layers(self, start: str, direction: str, max_layers: int = 0
                ) -> List[List[str]]:
        step = self.callers if direction == "up" else self.callees
        seen, layers, frontier, depth = {start}, [], deque([start]), 0
        while frontier:
            depth += 1
            if max_layers and depth > max_layers:
                break
            layer = []
            for _ in range(len(frontier)):
                current = frontier.popleft()
                for neighbour in sorted(step(current)):
                    if neighbour not in seen:
                        seen.add(neighbour)
                        layer.append(neighbour)
                        frontier.append(neighbour)
            if not layer:
                break
            layers.append(layer)
        return layers

    def callers_of(self, method: str, max_layers: int = 0) -> List[List[str]]:
        return self._layers(method, "up", max_layers)

    def callees_of(self, method: str, max_layers: int = 0) -> List[List[str]]:
        return self._layers(method, "down", max_layers)

    def summary(self) -> dict:
        return {"n_methods": len(self), "n_calls": self.n_edges,
                "n_roots": sum(1 for m in self.methods if not self.callers(m)),
                "n_leaves": sum(1 for m in self.methods if not self.callees(m))}


@dataclass(frozen=True)
class Space:
    """One method, everything above it, and everything below it."""

    seed: str
    upper_layers: Tuple[Tuple[str, ...], ...] = ()
    lower_layers: Tuple[Tuple[str, ...], ...] = ()

    @property
    def callers(self) -> Tuple[str, ...]:
        return tuple(m for layer in self.upper_layers for m in layer)

    @property
    def callees(self) -> Tuple[str, ...]:
        return tuple(m for layer in self.lower_layers for m in layer)

    @property
    def methods(self) -> FrozenSet[str]:
        return frozenset((self.seed,) + self.callers + self.callees)

    @property
    def size(self) -> int:
        return len(self.methods)

    def layer_of(self, method: str) -> Optional[Tuple[str, int]]:
        if method == self.seed:
            return ("seed", 0)
        for index, layer in enumerate(self.upper_layers, start=1):
            if method in layer:
                return ("caller", index)
        for index, layer in enumerate(self.lower_layers, start=1):
            if method in layer:
                return ("callee", index)
        return None

    def render(self, max_per_layer: int = 6) -> str:
        lines = []
        for index in range(len(self.upper_layers) - 1, -1, -1):
            members = list(self.upper_layers[index])
            lines.append(f"  callers L{index + 1}: " + _join(members, max_per_layer))
        lines.append(f"  SEED        {_short(self.seed)}")
        for index, layer in enumerate(self.lower_layers, start=1):
            lines.append(f"  callees L{index}: " + _join(list(layer), max_per_layer))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"seed": self.seed, "size": self.size,
                "callers": list(self.callers), "callees": list(self.callees),
                "n_caller_layers": len(self.upper_layers),
                "n_callee_layers": len(self.lower_layers)}


def _short(method: str) -> str:
    owner, _, name = method.partition("#")
    return f"{owner.rsplit('.', 1)[-1]}#{name}" if name else method


def _join(members: Sequence[str], limit: int) -> str:
    shown = ", ".join(_short(m) for m in members[:limit])
    extra = f" (+{len(members) - limit})" if len(members) > limit else ""
    return shown + extra


def build_space(graph: CallGraph, seed: str, max_layers: int = 0) -> Space:
    """The space around one method. ``max_layers`` of 0 means unbounded."""
    if seed not in graph:
        raise KeyError(f"{seed!r} is not a method in the call graph")
    return Space(seed=seed,
                 upper_layers=tuple(tuple(l) for l in graph.callers_of(seed, max_layers)),
                 lower_layers=tuple(tuple(l) for l in graph.callees_of(seed, max_layers)))


def build_spaces(graph: CallGraph, seeds: Iterable[str],
                 max_layers: int = 0) -> Dict[str, Space]:
    return {seed: build_space(graph, seed, max_layers)
            for seed in seeds if seed in graph}


def union_space(spaces: Iterable[Space]) -> FrozenSet[str]:
    """Every method inside any of these spaces, counted once."""
    out: Set[str] = set()
    for space in spaces:
        out |= space.methods
    return frozenset(out)
