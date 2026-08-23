"""Reading profiles, and comparing two of them.

Three numbers per method: total time, own time excluding callees, and
invocation count. Importers cover the formats a Java project already has,
so the tool does not ask anyone to change how they profile.

Nothing here samples anything. Measurement is the profiler's job; this
module's job is to say what changed between two profiles and to be honest
about when the difference is too small to be a difference.
"""

from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

PathLike = Union[str, Path]
METRICS = ("time", "own_time", "count")


@dataclass
class MethodProfile:
    """One method's numbers. ``None`` means the profiler never saw it."""

    method: str
    time: Optional[float] = None
    own_time: Optional[float] = None
    count: Optional[float] = None

    def get(self, metric: str) -> Optional[float]:
        if metric not in METRICS:
            raise ValueError(f"unknown metric {metric!r}; expected {METRICS}")
        return getattr(self, metric)

    @property
    def callee_time(self) -> Optional[float]:
        if self.time is None or self.own_time is None:
            return None
        return max(0.0, self.time - self.own_time)

    @property
    def own_share(self) -> Optional[float]:
        if not self.time:
            return None
        return (self.own_time or 0.0) / self.time

    @property
    def time_per_call(self) -> Optional[float]:
        if self.time is None or not self.count:
            return None
        return self.time / self.count


@dataclass
class Profile:
    """A whole run."""

    methods: Dict[str, MethodProfile] = field(default_factory=dict)
    label: str = ""
    unit: str = "ms"
    source: str = ""

    def __len__(self) -> int:
        return len(self.methods)

    def __contains__(self, method: str) -> bool:
        return method in self.methods

    def get(self, method: str) -> Optional[MethodProfile]:
        return self.methods.get(method)

    def value(self, method: str, metric: str = "time") -> Optional[float]:
        record = self.methods.get(method)
        return record.get(metric) if record else None

    def total(self, metric: str = "time") -> float:
        return sum(record.get(metric) or 0.0 for record in self.methods.values())

    def top(self, metric: str = "time", limit: int = 10) -> List[MethodProfile]:
        scored = [r for r in self.methods.values() if r.get(metric) is not None]
        return sorted(scored, key=lambda r: r.get(metric), reverse=True)[:limit]

    def summary(self) -> dict:
        measured = sum(1 for r in self.methods.values() if r.time is not None)
        return {"label": self.label, "n_methods": len(self.methods),
                "n_measured": measured, "unit": self.unit,
                "total_time": round(self.total("time"), 4)}


# ---------------------------------------------------------------------------
# Importers
# ---------------------------------------------------------------------------

_NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def _number(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    if not text or text in ("-", "--", "n/a", "N/A"):
        return None
    match = _NUM.search(text)
    return float(match.group(0)) if match else None


def from_csv(path: PathLike, label: str = "", unit: str = "ms") -> Profile:
    """``method,time,own_time,count``; column names matched loosely.

    This is the format every profiler can export to, and the one the other
    importers normalise into.
    """
    profile = Profile(label=label or Path(path).stem, unit=unit, source=str(path))
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fields = {str(name).lower().strip(): name
                  for name in (reader.fieldnames or [])}
        method_key = next((fields[k] for k in
                           ("method", "name", "signature", "symbol")
                           if k in fields), None)
        if method_key is None:
            raise ValueError(
                f"{path} has columns {list(fields)}; expected a 'method' column")

        def pick(row, *names):
            for name in names:
                if name in fields:
                    value = _number(row.get(fields[name]))
                    if value is not None:
                        return value
            return None

        for row in reader:
            method = str(row.get(method_key) or "").strip()
            if not method:
                continue
            profile.methods[method] = MethodProfile(
                method=method,
                time=pick(row, "time", "total time", "total_time", "cumulative",
                          "cumtime", "total"),
                own_time=pick(row, "own_time", "own time", "owntime",
                              "self time", "self", "tottime"),
                count=pick(row, "count", "invocations", "calls", "ncalls",
                           "hits"))
    return profile


def from_json(path: PathLike, label: str = "", unit: str = "ms") -> Profile:
    """``[{"method": ..., "time": ..., "own_time": ..., "count": ...}]``."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        unit = payload.get("unit", unit)
        label = label or payload.get("label", "")
        payload = payload.get("methods", [])
    profile = Profile(label=label or Path(path).stem, unit=unit, source=str(path))
    for item in payload:
        if not isinstance(item, dict):
            continue
        method = str(item.get("method") or item.get("name") or "").strip()
        if not method:
            continue
        profile.methods[method] = MethodProfile(
            method=method, time=_number(item.get("time")),
            own_time=_number(item.get("own_time") or item.get("self")),
            count=_number(item.get("count") or item.get("calls")))
    return profile


def from_jfr_summary(path: PathLike, label: str = "") -> Profile:
    """``jfr summary`` / ``jfr print --events ExecutionSample`` text output.

    Java Flight Recorder ships with the JDK, so this is the importer that
    needs no extra tool at all. It counts samples per method, which gives a
    relative time and a sample count but no own time; the missing field
    stays ``None`` rather than being invented.
    """
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    counts: Dict[str, int] = {}
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"(?:at\s+)?([\w.$]+)\.(\w+)\s*\(", stripped)
        if match:
            key = f"{match.group(1)}#{match.group(2)}"
            counts[key] = counts.get(key, 0) + 1
    profile = Profile(label=label or Path(path).stem, unit="samples",
                      source=str(path))
    for method, count in counts.items():
        profile.methods[method] = MethodProfile(method=method, time=float(count),
                                                own_time=float(count),
                                                count=float(count))
    return profile


def from_jmh_json(path: PathLike, label: str = "") -> Profile:
    """JMH's ``-rf json`` output, one entry per benchmark method.

    JMH measures benchmarks, not every method, so the resulting profile is
    sparse. It is still the right input when the question is what a change
    did to the benchmarks a project already runs.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    profile = Profile(label=label or Path(path).stem, source=str(path))
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        benchmark = str(entry.get("benchmark", "")).strip()
        if not benchmark:
            continue
        owner, _, name = benchmark.rpartition(".")
        key = f"{owner}#{name}" if owner else benchmark
        metric = entry.get("primaryMetric") or {}
        profile.unit = str(metric.get("scoreUnit", profile.unit))
        score = _number(metric.get("score"))
        profile.methods[key] = MethodProfile(method=key, time=score,
                                             own_time=score,
                                             count=_number(entry.get("measurementIterations")))
    return profile


LOADERS = {"csv": from_csv, "json": from_json, "jfr": from_jfr_summary,
           "jmh": from_jmh_json}


def load_profile(path: PathLike, fmt: str = "auto", label: str = "") -> Profile:
    if fmt == "auto":
        suffix = Path(path).suffix.lower()
        if suffix in (".csv", ".tsv"):
            fmt = "csv"
        elif suffix == ".json":
            text = Path(path).read_text(encoding="utf-8")[:400]
            fmt = "jmh" if '"primaryMetric"' in text or '"benchmark"' in text else "json"
        else:
            fmt = "jfr"
    if fmt not in LOADERS:
        raise ValueError(f"unknown profile format {fmt!r}; expected "
                         f"{sorted(LOADERS)} or 'auto'")
    return LOADERS[fmt](path, label=label)


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

@dataclass
class Delta:
    """What a change did to one method."""

    method: str
    before: Optional[float]
    after: Optional[float]
    metric: str = "time"

    @property
    def absolute(self) -> Optional[float]:
        if self.before is None or self.after is None:
            return None
        return self.after - self.before

    @property
    def relative(self) -> Optional[float]:
        if self.before in (None, 0) or self.after is None:
            return None
        return (self.after - self.before) / self.before

    @property
    def status(self) -> str:
        if self.before is None and self.after is not None:
            return "appeared"
        if self.after is None and self.before is not None:
            return "disappeared"
        if self.absolute is None:
            return "unmeasured"
        return "slower" if self.absolute > 0 else "faster" if self.absolute < 0 else "same"

    def to_dict(self) -> dict:
        return {"method": self.method, "metric": self.metric,
                "before": self.before, "after": self.after,
                "absolute": None if self.absolute is None else round(self.absolute, 6),
                "relative": None if self.relative is None else round(self.relative, 6),
                "status": self.status}


def compare(before: Profile, after: Profile, metric: str = "time",
            noise_floor: float = 0.0) -> List[Delta]:
    """Per-method deltas, largest increase first.

    ``noise_floor`` drops changes smaller than this fraction of the
    before-value. A profiler's run-to-run variation is real, and reporting
    a 0.3% "regression" as a finding trains a maintainer to ignore the
    tool.
    """
    methods = sorted(set(before.methods) | set(after.methods))
    deltas = []
    for method in methods:
        delta = Delta(method=method, before=before.value(method, metric),
                      after=after.value(method, metric), metric=metric)
        relative = delta.relative
        if noise_floor and relative is not None and abs(relative) < noise_floor:
            continue
        deltas.append(delta)
    return sorted(deltas, key=lambda d: -(d.absolute or 0.0))


def total_delta(before: Profile, after: Profile, metric: str = "time") -> float:
    return after.total(metric) - before.total(metric)
