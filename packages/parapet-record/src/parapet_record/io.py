"""Reading, writing and merging records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Union

from .schema import (RECORD_SCHEMA_VERSION, Budget, BudgetCheck, CostMeasure,
                     Exposure, HardeningRecord, Provenance, ReviewCost,
                     ToolResult)


def save_record(record: HardeningRecord, path: Union[str, Path]) -> Path:
    """Write a record as pretty JSON, with a stable key order."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=False),
                    encoding="utf-8")
    return path


def load_record(path: Union[str, Path]) -> HardeningRecord:
    """Read a record, refusing a schema version this build cannot read.

    Refusing loudly is the point. A record read under the wrong schema
    would produce a decision that looks valid and is not.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    version = payload.get("schema_version", "0")
    if version.split(".")[0] != RECORD_SCHEMA_VERSION.split(".")[0]:
        raise ValueError(
            f"{path} uses record schema {version}; this build reads "
            f"{RECORD_SCHEMA_VERSION}. Major versions are not compatible.")
    return _from_dict(payload)


def _from_dict(payload: dict) -> HardeningRecord:
    exposure = payload.get("exposure")
    budget = payload.get("budget")
    review = payload.get("review_cost")
    return HardeningRecord(
        schema_version=payload.get("schema_version", RECORD_SCHEMA_VERSION),
        record_id=payload.get("record_id", ""),
        exposure=Exposure(**exposure) if exposure else None,
        change_ref=payload.get("change_ref", ""),
        budget=Budget(**budget) if budget else None,
        costs=[CostMeasure(**item) for item in payload.get("costs", [])],
        budget_checks=[BudgetCheck(**item)
                       for item in payload.get("budget_checks", [])],
        review_cost=ReviewCost(**review) if review else None,
        attribution=payload.get("attribution", {}),
        verdict=payload.get("verdict", "unscored"),
        components=[ToolResult(component=item["component"],
                               provenance=Provenance(**item["provenance"]),
                               payload=item.get("payload", {}),
                               warnings=item.get("warnings", []))
                    for item in payload.get("components", [])],
        warnings=payload.get("warnings", []))


def merge_results(record: HardeningRecord,
                  results: Iterable[ToolResult]) -> HardeningRecord:
    """Fold component results into a record and re-decide.

    Later results do not overwrite earlier ones. Each component owns
    distinct fields, so a collision means two components claimed the same
    ground and that is a bug worth surfacing rather than resolving
    silently.
    """
    for result in results:
        record.add(result)
        payload = result.payload
        if "exposure" in payload and record.exposure is None:
            record.exposure = Exposure(**payload["exposure"])
        if "review_cost" in payload and record.review_cost is None:
            record.review_cost = ReviewCost(**payload["review_cost"])
        if "costs" in payload:
            record.costs.extend(CostMeasure(**item) for item in payload["costs"])
        if "attribution" in payload:
            overlap = set(record.attribution) & set(payload["attribution"])
            if overlap:
                record.warnings.append(
                    f"{result.component} re-wrote attribution keys "
                    f"{sorted(overlap)} already set by another component")
            record.attribution.update(payload["attribution"])
    record.decide()
    return record
