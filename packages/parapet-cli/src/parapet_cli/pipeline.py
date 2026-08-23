"""Chaining the components into one record.

Each stage is optional and each is skipped cleanly when its inputs are
absent, so the same command works for a project that only wants triage and
for one that measures everything. What a stage could not do is recorded as
a warning rather than assumed away: a record that silently omits the cost
check looks exactly like one that passed it, and that is the failure mode
worth designing against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

STAGES = ("triage", "scope", "attrib", "budget")


@dataclass
class StageResult:
    name: str
    ran: bool
    detail: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    record_path: Optional[Path] = None
    stages: List[StageResult] = field(default_factory=list)
    verdict: str = "unscored"
    warnings: List[str] = field(default_factory=list)

    def stage(self, name: str) -> Optional[StageResult]:
        return next((item for item in self.stages if item.name == name), None)

    def summary(self) -> str:
        lines = ["PARAPET hardening record"]
        for item in self.stages:
            mark = "ran    " if item.ran else "skipped"
            lines.append(f"  {mark}  {item.name:<8} {item.detail}")
        lines.append(f"  verdict: {self.verdict}")
        for warning in self.warnings:
            lines.append(f"  warning: {warning}")
        if self.record_path:
            lines.append(f"  record:  {self.record_path}")
        return "\n".join(lines)


def run_pipeline(out: Path,
                 issues: Optional[Path] = None,
                 issue_format: str = "auto",
                 pattern_set: str = "performance",
                 repo: Optional[Path] = None,
                 commit: str = "HEAD",
                 base: Optional[str] = None,
                 scope_depth: str = "neighbourhood",
                 before_profile: Optional[Path] = None,
                 after_profile: Optional[Path] = None,
                 profile_format: str = "auto",
                 graph: Optional[Path] = None,
                 source: Optional[Path] = None,
                 changed_methods: Optional[Sequence[str]] = None,
                 metric: str = "time",
                 budget_path: Optional[Path] = None,
                 record_id: str = "",
                 command: str = "") -> PipelineResult:
    """Run every stage whose inputs are present, into one record."""
    out = Path(out)
    result = PipelineResult()
    record = _new_record(record_id)

    # -- stage 1: what is this about ------------------------------------
    if issues is not None:
        result.stages.append(_run_triage(record, issues, issue_format,
                                         pattern_set, command))
    else:
        result.stages.append(StageResult(
            "triage", False, "no --issues given, so the record has no exposure"))
        result.warnings.append(
            "no exposure recorded; the record says what a change cost but not "
            "what it was for")

    # -- stage 2: how wide is the change --------------------------------
    if repo is not None:
        result.stages.append(_run_scope(record, repo, commit, base, scope_depth,
                                        command))
    else:
        result.stages.append(StageResult(
            "scope", False, "no --repo given, so review cost is unknown"))

    # -- stage 3: what did it cost, and where ---------------------------
    if before_profile and after_profile and (graph or source):
        result.stages.append(_run_attrib(record, before_profile, after_profile,
                                         profile_format, graph, source,
                                         changed_methods, metric, command))
    else:
        missing = [name for name, value in
                   (("--before", before_profile), ("--after", after_profile),
                    ("--graph or --source", graph or source)) if not value]
        result.stages.append(StageResult(
            "attrib", False, f"missing {', '.join(missing)}"))

    # -- stage 4: does it fit ------------------------------------------
    if budget_path is not None:
        result.stages.append(_run_budget(record, budget_path))
    else:
        result.stages.append(StageResult(
            "budget", False, "no --budget given, so nothing was decided"))

    result.verdict = _decide(record)
    result.warnings.extend(getattr(record, "warnings", []) or [])
    result.record_path = _save(record, out, record_id)
    return result


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def _run_triage(record, issues: Path, fmt: str, pattern_set: str,
                command: str) -> StageResult:
    try:
        from parapet_triage import Triager, load_pattern_set, load_reports
    except ImportError:
        return StageResult("triage", False,
                           "parapet-triage is not installed")
    reports = load_reports(issues, fmt)
    if not reports:
        return StageResult("triage", False, f"no reports found in {issues}")
    triager = Triager(pattern_set=load_pattern_set(pattern_set))
    verdicts = [triager.classify_text(r.text, r.identifier) for r in reports]
    matched = [(r, v) for r, v in zip(reports, verdicts) if v.is_match]
    if not matched:
        return StageResult("triage", True,
                           f"{len(reports)} report(s), none matched "
                           f"{pattern_set}")
    report, verdict = matched[0]
    from parapet_triage.record import exposure_payload
    payload = exposure_payload(report, verdict,
                               "security" if pattern_set.startswith("security")
                               else "performance")
    _set_exposure(record, payload)
    return StageResult("triage", True,
                       f"{len(matched)}/{len(reports)} matched; recorded "
                       f"{report.identifier} ({', '.join(verdict.patterns[:3])})",
                       {"n_matched": len(matched)})


def _run_scope(record, repo: Path, commit: str, base: Optional[str],
               depth: str, command: str) -> StageResult:
    try:
        from parapet_scope import analyse, build_diff_dsm, load_revision
        from parapet_scope.classify import ScopeVerdict
        from parapet_scope.record import review_cost_payload
    except ImportError:
        return StageResult("scope", False, "parapet-scope is not installed")
    from parapet_scope.gitsource import GitError
    try:
        revision = load_revision(repo, commit, base, depth)
    except GitError as exc:
        return StageResult("scope", False, str(exc))
    if not revision.changed:
        return StageResult("scope", True, f"{revision.short} changed no Java files")
    diff = build_diff_dsm(revision.before, revision.after, revision.changed,
                          change_ref=revision.short)
    verdict = analyse(diff, revision.before, revision.after)
    _set_review_cost(record, review_cost_payload(verdict, diff))
    _set_change_ref(record, revision.commit)
    detail = (f"{revision.short}: {verdict.scope}"
              + (f", {verdict.design_pattern}" if verdict.design_pattern else "")
              + f"; {verdict.n_production_files}p {verdict.n_test_files}t")
    return StageResult("scope", True, detail, {"verdict": verdict.to_dict()})


def _run_attrib(record, before: Path, after: Path, fmt: str,
                graph_path: Optional[Path], source: Optional[Path],
                changed_methods: Optional[Sequence[str]], metric: str,
                command: str) -> StageResult:
    try:
        from parapet_attrib import attribute, load_graph, load_profile
        from parapet_attrib.record import cost_payload
        from parapet_attrib.space import CallGraph
    except ImportError:
        return StageResult("attrib", False, "parapet-attrib is not installed")

    if graph_path:
        graph = load_graph(graph_path)
    else:
        from parapet_attrib.javacalls import build_call_graph
        root = Path(source)
        sources = {str(p.relative_to(root)).replace("\\", "/"):
                   p.read_text(encoding="utf-8", errors="replace")
                   for p in root.rglob("*.java")}
        java_graph = build_call_graph(sources)
        graph = CallGraph.from_edges(java_graph.to_edge_list(),
                                     java_graph.methods.keys())

    before_profile = load_profile(before, fmt, label="before")
    after_profile = load_profile(after, fmt, label="after")
    methods = list(changed_methods or [])
    if not methods:
        return StageResult("attrib", False,
                           "no changed methods given; pass --changed-methods")
    result = attribute(graph, before_profile, after_profile, methods,
                       metric=metric,
                       change_ref=_get_change_ref(record) or "")
    _add_costs(record, cost_payload(result, before_profile, after_profile))
    _set_attribution(record, result.to_dict())
    _add_warnings(record, result.warnings)
    relative = result.relative_delta
    detail = (f"total {metric} {result.total_before:.4g} -> "
              f"{result.total_after:.4g}"
              + (f" ({relative:+.1%})" if relative is not None else "")
              + f"; landed {result.where()}")
    return StageResult("attrib", True, detail, {"attribution": result.to_dict()})


def _run_budget(record, budget_path: Path) -> StageResult:
    from .budget import load_budget
    try:
        budget = load_budget(budget_path)
    except (ValueError, RuntimeError) as exc:
        return StageResult("budget", False, str(exc))
    try:
        from parapet_record.schema import BudgetError, check_budget
    except ImportError:
        _set_budget(record, budget)
        return StageResult("budget", False,
                           "parapet-record is not installed, so the budget was "
                           "recorded but not checked")
    _set_budget(record, budget)
    costs = getattr(record, "costs", None) or record.get("costs", [])
    if not costs:
        return StageResult("budget", False,
                           "no measured cost to check against the budget")
    checks = []
    for cost in costs:
        try:
            checks.append(check_budget(budget, cost))
        except BudgetError as exc:
            _add_warnings(record, [str(exc)])
    _set_budget_checks(record, checks)
    fitting = sum(1 for check in checks if check.fits)
    return StageResult("budget", True,
                       f"{fitting}/{len(checks)} dimension(s) fit")


# ---------------------------------------------------------------------------
# Record access, tolerant of parapet-record being absent
# ---------------------------------------------------------------------------

def _new_record(record_id: str):
    try:
        from parapet_record import HardeningRecord
        return HardeningRecord(record_id=record_id or "record")
    except ImportError:
        return {"schema_version": "1.0.0", "record_id": record_id or "record",
                "costs": [], "budget_checks": [], "components": [],
                "warnings": ["parapet-record is not installed, so this record "
                             "has no input hashes or environment profile"],
                "verdict": "unscored"}


def _is_dict(record) -> bool:
    return isinstance(record, dict)


def _set_exposure(record, payload: Dict[str, Any]) -> None:
    if _is_dict(record):
        record["exposure"] = payload
        return
    from parapet_record import Exposure
    record.exposure = Exposure(**payload)


def _set_review_cost(record, payload: Dict[str, Any]) -> None:
    if _is_dict(record):
        record["review_cost"] = payload
        return
    from parapet_record import ReviewCost
    record.review_cost = ReviewCost(**payload)


def _set_change_ref(record, value: str) -> None:
    if _is_dict(record):
        record["change_ref"] = value
    else:
        record.change_ref = value


def _get_change_ref(record) -> str:
    return record.get("change_ref", "") if _is_dict(record) else record.change_ref


def _add_costs(record, payloads: Sequence[Dict[str, Any]]) -> None:
    if _is_dict(record):
        record.setdefault("costs", []).extend(payloads)
        return
    from parapet_record import CostMeasure
    record.costs.extend(CostMeasure(**item) for item in payloads)


def _set_attribution(record, payload: Dict[str, Any]) -> None:
    if _is_dict(record):
        record["attribution"] = payload
    else:
        record.attribution.update(payload)


def _set_budget(record, budget) -> None:
    if _is_dict(record):
        record["budget"] = budget if isinstance(budget, dict) else budget.to_dict()
    else:
        record.budget = budget


def _set_budget_checks(record, checks) -> None:
    if _is_dict(record):
        record["budget_checks"] = [check.to_dict() for check in checks]
    else:
        record.budget_checks.extend(checks)


def _add_warnings(record, warnings: Sequence[str]) -> None:
    if _is_dict(record):
        record.setdefault("warnings", []).extend(warnings)
    else:
        record.warnings.extend(warnings)


def _decide(record) -> str:
    if _is_dict(record):
        checks = record.get("budget_checks", [])
        if not checks:
            return "unscored"
        if any(check.get("interval_fits") is None for check in checks):
            return "unscored"
        return ("admitted" if all(check["fits"] and check["interval_fits"]
                                  for check in checks) else "overrun")
    return record.decide()


def _save(record, out: Path, record_id: str) -> Path:
    import json
    out = Path(out)
    if out.is_dir() or not out.suffix:
        out.mkdir(parents=True, exist_ok=True)
        out = out / f"{record_id or 'record'}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if _is_dict(record):
        out.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return out
    from parapet_record import save_record
    return save_record(record, out)
