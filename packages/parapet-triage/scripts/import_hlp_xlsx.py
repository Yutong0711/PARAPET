"""Turn the published ``HLP List.xlsx`` into the YAML pattern set we ship.

Run once, when the upstream data package changes. The output is vendored
into ``src/parapet_triage/data/`` so a user never needs the workbook.

    python scripts/import_hlp_xlsx.py --workbook "HLP List.xlsx" \
        --out src/parapet_triage/data/hlp_set_performance.yaml

The workbook is CC BY 4.0 (doi:10.5281/zenodo.10944186); the NOTICE file
carries the attribution.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

import openpyxl
import yaml

SHEET = "Saturated HLP Set"
CATEGORIES = {"LEX", "STR", "SEM", "PRF"}


def clean(value) -> str:
    return "" if value is None else re.sub(r"\s+", " ", str(value)).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--sheet", default=SHEET)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    workbook = openpyxl.load_workbook(args.workbook, read_only=True, data_only=True)
    rows = [list(r) for r in workbook[args.sheet].iter_rows(values_only=True)]
    workbook.close()

    patterns, seen_defs = [], {}
    for index, row in enumerate(rows[1:], start=1):
        category = clean(row[0])
        name = clean(row[1]) if len(row) > 1 else ""
        definition = clean(row[2]) if len(row) > 2 else ""
        if not name:
            continue
        entry = {"id": f"HLP{index:03d}", "name": name,
                 "category": category if category in CATEGORIES else "LEX",
                 "definition": definition}
        # Two rows in the published set share a definition; keep both and
        # flag the duplicate rather than dropping one silently.
        if definition and definition in seen_defs:
            entry["note"] = (f"identical definition to {seen_defs[definition]} "
                             "in the published set")
        elif definition:
            seen_defs[definition] = name
        patterns.append(entry)

    payload = {
        "set_id": "performance-v1",
        "description": ("The 80 heuristic linguistic patterns of Zhao, Xiao "
                        "and Wong (TSE 2024), transcribed from the published "
                        "data package."),
        "source": {"doi": "10.5281/zenodo.10944186",
                   "paper_doi": "10.1109/TSE.2024.3390623",
                   "license": "CC-BY-4.0"},
        "patterns": patterns,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8")

    counts = Counter(p["category"] for p in patterns)
    print(f"wrote {args.out}: {len(patterns)} patterns {dict(counts)}")


if __name__ == "__main__":
    main()
