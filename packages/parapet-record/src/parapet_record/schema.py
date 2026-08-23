"""Dataclasses for the hardening record, versioned.

The schema is deliberately small. A field earns its place by being
something a maintainer, a downstream consumer, a packager or the next
contributor would read, which is the four-reader test the service budget
has to pass.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

RECORD_SCHEMA_VERSION = "1.0.0"

# Units a budget may be written in. Anything else is rejected at parse time
# rather than silently compared against a number in another unit.
LATENCY_UNITS = {"ns", "us", "ms", "s"}
MEMORY_UNITS = {"b", "kb", "mb", "gb"}
RELATIVE_UNITS = {"%", "x"}
_LIMIT = re.compile(r"^\s*(?P<value>-?\d+(?:\.\d+)?)\s*(?P<unit>%|x|[a-zA-Z]+)\s*$")


class BudgetError(ValueError):
    """A service budget that cannot be compared against a measurement."""


@dataclass
class Provenance:
    """Who produced a record part, from what, in what environment."""

    tool: str
    tool_version: str
    schema_version: str = RECORD_SCHEMA_VERSION
    created_at: str = ""
    inputs: Dict[str, str] = field(default_factory=dict)   # name -> sha256
    environment: Dict[str, str] = field(default_factory=dict)
    command: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Exposure:
    """One weakness or inefficiency instance in one piece of code.

    ``reproducer`` is what makes an exposure actionable: an input that
    triggers it, a checker trace, or a failing test. An exposure without
    one can be classified but not verified, and the record says so.
    """

    identifier: str
    kind: str = "unknown"            # security | performance | unknown
    cwe: Optional[str] = None
    title: str = ""
    text: str = ""
    reproducer: Optional[str] = None
    source: str = ""                 # advisory id, issue url, file path
    labels: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    evidence: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_reproducer(self) -> bool:
        return bool(self.reproducer)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CostMeasure:
    """One measured cost dimension, with its interval.

    The interval is not decoration. A change is admitted only when the
    whole interval fits the budget, so a measurement without one cannot be
    used for a budget decision and ``interval_low`` being ``None`` is how
    that is recorded.
    """

    dimension: str                   # latency | memory | cpu
    value: float
    unit: str
    interval_low: Optional[float] = None
    interval_high: Optional[float] = None
    baseline: Optional[float] = None
    workload: str = ""
    n_samples: Optional[int] = None
    settled: Optional[bool] = None

    @property
    def has_interval(self) -> bool:
        return self.interval_low is not None and self.interval_high is not None

    @property
    def relative_change(self) -> Optional[float]:
        if self.baseline in (None, 0):
            return None
        return (self.value - self.baseline) / self.baseline

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Budget:
    """A maintainer-declared limit on what security may cost at run time.

    Written by the maintainer, versioned, and read by four audiences: the
    maintainer, the downstream consumer, the packager and the next
    contributor. Limits are strings with units, e.g. ``"5%"``, ``"20ms"``,
    ``"64mb"``, so a number can never be compared against a different unit
    by accident.
    """

    project: str = ""
    version: str = "1"
    limits: Dict[str, str] = field(default_factory=dict)   # dimension -> limit
    binding: List[str] = field(default_factory=list)       # which limits decide
    workloads: List[str] = field(default_factory=list)
    authority: str = ""                                    # who may change it
    notes: str = ""

    def parse_limit(self, dimension: str) -> Optional[tuple]:
        """``("5", "%")`` -> ``(5.0, "%")``; ``None`` when undeclared."""
        raw = self.limits.get(dimension)
        if raw is None:
            return None
        match = _LIMIT.match(str(raw))
        if not match:
            raise BudgetError(
                f"limit for {dimension!r} is {raw!r}, which has no readable "
                "unit; use a form like '5%', '1.2x', '20ms' or '64mb'")
        unit = match.group("unit").lower()
        if unit not in LATENCY_UNITS | MEMORY_UNITS | RELATIVE_UNITS:
            raise BudgetError(
                f"limit for {dimension!r} uses unit {unit!r}; expected one of "
                f"{sorted(LATENCY_UNITS | MEMORY_UNITS | RELATIVE_UNITS)}")
        return float(match.group("value")), unit

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BudgetCheck:
    """The admit-or-overrun decision for one dimension."""

    dimension: str
    limit: str
    measured: float
    unit: str
    fits: bool
    interval_fits: Optional[bool] = None
    overrun: Optional[float] = None
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReviewCost:
    """What a change costs a human to review, not what it costs at run time.

    The distinction matters: a change that is free at run time and touches
    forty files is not cheap. These fields come from the change-scope
    analysis and are the second half of what a maintainer is deciding on.
    """

    n_production_files: int = 0
    n_test_files: int = 0
    scope: str = "unknown"           # localized | design-level | unknown
    design_pattern: Optional[str] = None
    cochange_patterns: List[str] = field(default_factory=list)
    added_dependencies: int = 0
    removed_dependencies: int = 0
    added_files: List[str] = field(default_factory=list)
    removed_files: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ToolResult:
    """One component's contribution to a record."""

    component: str
    provenance: Provenance
    payload: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"component": self.component,
                "provenance": self.provenance.to_dict(),
                "payload": self.payload, "warnings": list(self.warnings)}


@dataclass
class HardeningRecord:
    """What reaches the maintainer.

    Four questions, in the order the paper's step 4 answers them: what was
    removed, the check that proves it, what it cost, and how to reproduce
    both.
    """

    schema_version: str = RECORD_SCHEMA_VERSION
    record_id: str = ""
    exposure: Optional[Exposure] = None
    change_ref: str = ""                       # commit, patch id or PR
    budget: Optional[Budget] = None
    costs: List[CostMeasure] = field(default_factory=list)
    budget_checks: List[BudgetCheck] = field(default_factory=list)
    review_cost: Optional[ReviewCost] = None
    attribution: Dict[str, Any] = field(default_factory=dict)
    verdict: str = "unscored"                  # admitted | overrun | unscored
    components: List[ToolResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add(self, result: ToolResult) -> "HardeningRecord":
        self.components.append(result)
        self.warnings.extend(result.warnings)
        return self

    @property
    def reproducible(self) -> bool:
        """Every component recorded its inputs and its environment."""
        return bool(self.components) and all(
            item.provenance.inputs and item.provenance.environment
            for item in self.components)

    def decide(self) -> str:
        """Set and return the verdict from the budget checks.

        A change is admitted only when every checked dimension fits and,
        where an interval exists, the whole interval fits. A dimension with
        no interval cannot admit on its own; it leaves the record
        ``unscored`` so the gap is visible instead of assumed away.
        """
        if not self.budget_checks:
            self.verdict = "unscored"
            return self.verdict
        if any(check.interval_fits is None for check in self.budget_checks):
            self.verdict = "unscored"
            self.warnings.append(
                "at least one cost has no interval, so the budget decision "
                "cannot be made; re-measure until the interval settles")
            return self.verdict
        fits = all(check.fits and check.interval_fits
                   for check in self.budget_checks)
        self.verdict = "admitted" if fits else "overrun"
        return self.verdict

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "exposure": self.exposure.to_dict() if self.exposure else None,
            "change_ref": self.change_ref,
            "budget": self.budget.to_dict() if self.budget else None,
            "costs": [cost.to_dict() for cost in self.costs],
            "budget_checks": [check.to_dict() for check in self.budget_checks],
            "review_cost": self.review_cost.to_dict() if self.review_cost else None,
            "attribution": self.attribution,
            "verdict": self.verdict,
            "components": [item.to_dict() for item in self.components],
            "warnings": list(self.warnings),
        }


def check_budget(budget: Budget, cost: CostMeasure) -> BudgetCheck:
    """Compare one measurement against the declared limit for its dimension.

    Relative limits (``%``, ``x``) need a baseline; absolute limits do not.
    A dimension the budget does not declare is not a pass, it is a
    non-decision, and the returned check says so.
    """
    parsed = budget.parse_limit(cost.dimension)
    if parsed is None:
        return BudgetCheck(dimension=cost.dimension, limit="(undeclared)",
                           measured=cost.value, unit=cost.unit, fits=True,
                           interval_fits=None,
                           reason="the budget declares no limit for this "
                                  "dimension, so it cannot decide")
    limit_value, limit_unit = parsed

    if limit_unit in RELATIVE_UNITS:
        relative = cost.relative_change
        if relative is None:
            return BudgetCheck(cost.dimension, str(budget.limits[cost.dimension]),
                               cost.value, cost.unit, fits=False,
                               interval_fits=None,
                               reason="a relative limit needs a baseline "
                                      "measurement and none was recorded")
        threshold = limit_value / 100.0 if limit_unit == "%" else limit_value - 1.0
        fits = relative <= threshold
        interval_fits = None
        if cost.has_interval and cost.baseline:
            high = (cost.interval_high - cost.baseline) / cost.baseline
            interval_fits = high <= threshold
        return BudgetCheck(cost.dimension, str(budget.limits[cost.dimension]),
                           cost.value, cost.unit, fits, interval_fits,
                           overrun=max(0.0, relative - threshold),
                           reason="relative to the recorded baseline")

    if limit_unit != cost.unit.lower():
        raise BudgetError(
            f"budget limits {cost.dimension} in {limit_unit!r} but the "
            f"measurement is in {cost.unit!r}; convert one of them rather "
            "than comparing across units")
    added = cost.value - (cost.baseline or 0.0)
    fits = added <= limit_value
    interval_fits = None
    if cost.has_interval:
        interval_fits = (cost.interval_high - (cost.baseline or 0.0)) <= limit_value
    return BudgetCheck(cost.dimension, str(budget.limits[cost.dimension]),
                       cost.value, cost.unit, fits, interval_fits,
                       overrun=max(0.0, added - limit_value),
                       reason="absolute added cost")
