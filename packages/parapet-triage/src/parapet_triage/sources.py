"""Getting issue reports and advisories in.

Step 1 of the pipeline ingests an exposure. In practice that arrives in
one of four shapes, and this module normalises all of them to
``(identifier, text)`` pairs so the classifier does not care which.

Nothing here reaches the network. An advisory feed is read from a file you
downloaded, so a run is reproducible and an air-gapped project can use the
tool at all.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

PathLike = Union[str, Path]


@dataclass
class Report:
    """One issue report or advisory, flattened."""

    identifier: str
    title: str = ""
    body: str = ""
    cwe: Optional[str] = None
    reproducer: Optional[str] = None
    source: str = ""
    extra: Dict[str, str] = None

    @property
    def text(self) -> str:
        """Title and body joined, with the title kept as its own sentence."""
        title = self.title.strip()
        body = self.body.strip()
        if title and not title.endswith((".", "!", "?")):
            title += "."
        return (title + " " + body).strip()

    def to_dict(self) -> dict:
        return {"identifier": self.identifier, "title": self.title,
                "body": self.body, "cwe": self.cwe,
                "reproducer": self.reproducer, "source": self.source}


# ---------------------------------------------------------------------------
# CSV and JSON
# ---------------------------------------------------------------------------

_ID_KEYS = ("id", "key", "identifier", "issue", "issue_key", "bug id", "number")
_TITLE_KEYS = ("title", "summary", "subject", "name")
_BODY_KEYS = ("body", "description", "text", "content", "details")


def _pick(row: Dict[str, str], keys: Sequence[str]) -> str:
    lowered = {str(k).lower().strip(): v for k, v in row.items() if k}
    for key in keys:
        value = lowered.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def from_csv(path: PathLike) -> List[Report]:
    """A CSV with an id column and a title or body column.

    Column names are matched case-insensitively against a list of common
    spellings, so an export from Jira, GitHub or a spreadsheet usually
    works without renaming anything.
    """
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        rows = list(reader)
    if not rows:
        return []
    sample = rows[0]
    if not (_pick(sample, _TITLE_KEYS) or _pick(sample, _BODY_KEYS)):
        raise ValueError(
            f"{path} has columns {list(sample)}; expected one of "
            f"{list(_TITLE_KEYS)} or {list(_BODY_KEYS)} to hold the report text")
    out = []
    for index, row in enumerate(rows, start=1):
        identifier = _pick(row, _ID_KEYS) or f"row-{index}"
        out.append(Report(identifier=identifier,
                          title=_pick(row, _TITLE_KEYS),
                          body=_pick(row, _BODY_KEYS),
                          source=str(path)))
    return out


def from_json(path: PathLike) -> List[Report]:
    """A JSON list of objects, or an object with an ``issues`` list."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("issues") or payload.get("items") or [payload]
    out = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            continue
        out.append(Report(identifier=_pick(item, _ID_KEYS) or f"item-{index}",
                          title=_pick(item, _TITLE_KEYS),
                          body=_pick(item, _BODY_KEYS),
                          source=str(path)))
    return out


# ---------------------------------------------------------------------------
# Advisories
# ---------------------------------------------------------------------------

_CWE = re.compile(r"CWE-\d+", re.I)
_REPRODUCER_HINT = re.compile(
    r"(proof[- ]of[- ]concept|reproducer|crash input|oss-fuzz|clusterfuzz|"
    r"asan|ubsan|msan|valgrind|testcase|test case)", re.I)


def from_osv(path: PathLike) -> List[Report]:
    """OSV advisories: one JSON document, or a directory of them.

    OSV is the format GitHub, PyPI, crates.io and the Go vulnerability
    database all publish, so it is the widest single door into step 1.
    A ``credits``, ``references`` or ``details`` field mentioning a proof
    of concept is recorded as a reproducer hint, because an exposure with
    a reproducer can be verified and one without cannot.
    """
    path = Path(path)
    files = sorted(path.glob("**/*.json")) if path.is_dir() else [path]
    out = []
    for file in files:
        try:
            payload = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for advisory in (payload if isinstance(payload, list) else [payload]):
            if not isinstance(advisory, dict) or "id" not in advisory:
                continue
            out.append(_osv_report(advisory, file))
    return out


def _osv_report(advisory: dict, file: Path) -> Report:
    details = advisory.get("details", "") or ""
    summary = advisory.get("summary", "") or ""
    references = " ".join(
        str(ref.get("url", "")) for ref in advisory.get("references", [])
        if isinstance(ref, dict))
    blob = " ".join([summary, details, references])

    cwe = None
    database = advisory.get("database_specific") or {}
    if isinstance(database, dict):
        listed = database.get("cwe_ids") or database.get("cwes")
        if isinstance(listed, list) and listed:
            cwe = str(listed[0])
    if cwe is None:
        found = _CWE.search(blob)
        cwe = found.group(0).upper() if found else None

    hint = _REPRODUCER_HINT.search(blob)
    return Report(identifier=str(advisory["id"]), title=summary, body=details,
                  cwe=cwe, reproducer=hint.group(0) if hint else None,
                  source=str(file))


def from_github_issues(path: PathLike) -> List[Report]:
    """The JSON the GitHub issues API returns, saved to a file.

    ``gh issue list --json number,title,body --limit 1000 > issues.json``
    produces exactly this.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("items", [])
    out = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        number = item.get("number") or item.get("id")
        out.append(Report(identifier=str(number) if number else "?",
                          title=str(item.get("title") or ""),
                          body=str(item.get("body") or ""),
                          source=str(path)))
    return out


def from_text(path: PathLike) -> List[Report]:
    """A plain text or Markdown file, treated as one report."""
    path = Path(path)
    return [Report(identifier=path.stem, body=path.read_text(encoding="utf-8"),
                   source=str(path))]


LOADERS = {"csv": from_csv, "json": from_json, "osv": from_osv,
           "github": from_github_issues, "text": from_text}


def detect_format(path: PathLike) -> str:
    """Guess the format from the extension and, for JSON, the content."""
    path = Path(path)
    if path.is_dir():
        return "osv"
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv"):
        return "csv"
    if suffix in (".txt", ".md", ".rst"):
        return "text"
    if suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return "json"
        first = payload[0] if isinstance(payload, list) and payload else payload
        if isinstance(first, dict):
            if "schema_version" in first and "affected" in first:
                return "osv"
            if str(first.get("id", "")).upper().startswith(("GHSA-", "CVE-", "OSV-")):
                return "osv"
            if "number" in first and "title" in first:
                return "github"
        return "json"
    return "text"


def load_reports(path: PathLike, fmt: str = "auto") -> List[Report]:
    """Load reports from a path, detecting the format unless told."""
    chosen = detect_format(path) if fmt == "auto" else fmt
    if chosen not in LOADERS:
        raise ValueError(f"unknown format {chosen!r}; expected one of "
                         f"{sorted(LOADERS)} or 'auto'")
    return LOADERS[chosen](path)
