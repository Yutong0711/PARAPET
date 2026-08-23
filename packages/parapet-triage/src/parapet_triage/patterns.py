"""Loading pattern sets.

Two sets ship with the package. ``performance`` is the published set of 80
patterns; ``security`` is a smaller set aimed at hardening work, kept in
the same format so a project can extend either or write its own.

A pattern set is a YAML file:

.. code-block:: yaml

    set_id: my-set-v1
    patterns:
      - id: MY001
        name: unbounded_read
        category: STR
        definition: '{"read" | "reads"} + {"without" | "no"} + {"limit" | "bound"}'
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import yaml

DATA_DIR = Path(__file__).parent / "data"
BUILTIN_SETS = {
    "performance": DATA_DIR / "hlp_set_performance.yaml",
    "security": DATA_DIR / "hlp_set_security.yaml",
}


@dataclass
class PatternSet:
    set_id: str
    patterns: List[Dict[str, str]]
    description: str = ""
    source: Optional[Dict[str, str]] = None
    path: Optional[Path] = None

    def __len__(self) -> int:
        return len(self.patterns)

    @property
    def names(self) -> List[str]:
        return [item["name"] for item in self.patterns]

    def categories(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for item in self.patterns:
            key = item.get("category", "LEX")
            counts[key] = counts.get(key, 0) + 1
        return counts


def load_pattern_set(name_or_path: Union[str, Path] = "performance") -> PatternSet:
    """Load a built-in set by name, or any YAML file by path."""
    key = str(name_or_path)
    path = BUILTIN_SETS.get(key)
    if path is None:
        path = Path(name_or_path)
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found, and {key!r} is not a built-in set. "
                f"Built-in sets: {sorted(BUILTIN_SETS)}")
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    patterns = payload.get("patterns") or []
    if not patterns:
        raise ValueError(f"{path} declares no patterns")
    for index, item in enumerate(patterns):
        if "name" not in item:
            raise ValueError(f"{path}: pattern {index} has no name")
        item.setdefault("id", f"P{index + 1:03d}")
        item.setdefault("category", "LEX")
        item.setdefault("definition", "")
    return PatternSet(set_id=payload.get("set_id", Path(path).stem),
                      patterns=patterns,
                      description=payload.get("description", ""),
                      source=payload.get("source"),
                      path=Path(path))


def save_pattern_set(pattern_set: PatternSet, path: Union[str, Path]) -> Path:
    payload = {"set_id": pattern_set.set_id,
               "description": pattern_set.description,
               "patterns": pattern_set.patterns}
    if pattern_set.source:
        payload["source"] = pattern_set.source
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True,
                                   width=100), encoding="utf-8")
    return path
