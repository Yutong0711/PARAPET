"""The service budget: what a project says security may cost at run time.

A budget is a small YAML file a maintainer writes once and commits. It has
four readers, and the format is shaped by all four:

* the maintainer, who has to be able to write it without a meeting;
* the downstream consumer, who wants to know whether the project's
  tolerance is tighter or looser than their own;
* the packager, deciding whether to carry a hardened build;
* the next contributor, learning what is worth proposing.

Whoever can edit this file decides how much security the project buys, so
``authority`` is a required field. A budget that nobody owns is a budget
anybody can lower.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
    HAVE_YAML = True
except ImportError:  # pragma: no cover
    HAVE_YAML = False

PathLike = Union[str, Path]

DEFAULT_FILENAME = "parapet-budget.yaml"

TEMPLATE = """\
# The price in service quality this project will pay for security.
#
# Whoever can edit this file decides how much security the project buys.
# Lowering a limit quietly is an attack: hardening the project would
# otherwise accept starts failing its own budget check, the defences
# weaken, and no security code changed for a reviewer to see. Name the
# authority, and review changes to this file the way you review a change
# to a signing key.

project: {project}
version: 1

# The authority: who may change these limits, and what evidence a change
# needs. Free text, but say something specific enough to hold.
authority: >-
  Changes require review by two maintainers and a note in the pull request
  explaining what workload evidence justified the new limit.

# Limits on added cost, relative to the baseline measured on the workloads
# below. Use a unit: "5%" or "1.2x" for relative, "20ms" or "64mb" for
# absolute. Leave a dimension out and it does not decide anything.
limits:
  latency: "5%"
  memory: "10%"
  # cpu: "5%"

# Which limits actually bind the decision. A limit not listed here is
# recorded and reported but does not block a change.
binding:
  - latency

# The workloads a cost claim must be measured on. A budget without
# workloads cannot be checked, because "5% slower" is meaningless until
# someone says "at what".
workloads:
  - "bench/read-throughput"
  - "bench/cold-start"

notes: >-
  Written {date}. Baselines were taken on the workloads above; see
  docs/measurement.md for the environment.
"""


def load_budget(path: PathLike):
    """Read a budget file into a ``parapet_record.Budget``.

    Falls back to a plain dict when ``parapet-record`` is not installed,
    so the CLI still reports the limits even in a minimal install.
    """
    if not HAVE_YAML:
        raise RuntimeError("reading a budget needs PyYAML: pip install PyYAML")
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain a mapping")

    missing = [key for key in ("limits",) if key not in payload]
    if missing:
        raise ValueError(f"{path} is missing required key(s): {missing}")
    if not payload.get("authority"):
        raise ValueError(
            f"{path} has no 'authority' field. A budget that names nobody as "
            "its owner cannot be defended; say who may change it.")

    try:
        from parapet_record import Budget
    except ImportError:  # pragma: no cover
        return payload
    return Budget(project=str(payload.get("project", "")),
                  version=str(payload.get("version", "1")),
                  limits={str(k): str(v)
                          for k, v in (payload.get("limits") or {}).items()},
                  binding=[str(item) for item in (payload.get("binding") or [])],
                  workloads=[str(item) for item in (payload.get("workloads") or [])],
                  authority=str(payload.get("authority", "")),
                  notes=str(payload.get("notes", "")))


def write_budget_template(path: PathLike, project: str = "my-project") -> Path:
    """Write a commented starter budget for a maintainer to edit."""
    from datetime import date

    path = Path(path)
    if path.is_dir():
        path = path / DEFAULT_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(project=project, date=date.today().isoformat()),
                    encoding="utf-8")
    return path


def _field(budget, name, default):
    """Read one field from a ``Budget`` or from the plain-dict fallback.

    Written out rather than ``getattr(b, n, None) or b.get(n, d)``, because
    an empty list is falsy: that idiom falls through to the dict branch
    whenever a field is legitimately empty, and a dataclass has no ``get``.
    A budget with no ``binding`` is the common case, so the bug fires on
    ordinary input rather than on an edge case.
    """
    if isinstance(budget, dict):
        return budget.get(name, default)
    return getattr(budget, name, default)


def describe(budget) -> str:
    """A one-screen summary of what a budget allows."""
    limits = _field(budget, "limits", {})
    binding = _field(budget, "binding", [])
    workloads = _field(budget, "workloads", [])
    authority = _field(budget, "authority", "")
    lines = ["service budget:"]
    for dimension, limit in limits.items():
        mark = " (binding)" if dimension in binding else ""
        lines.append(f"  {dimension:<10} {limit}{mark}")
    lines.append(f"  workloads: {', '.join(workloads) or 'none declared'}")
    if not workloads:
        lines.append("  warning: no workloads declared, so a cost claim "
                     "cannot be checked against this budget")
    lines.append(f"  authority: {(authority or 'UNSET')[:100]}")
    return "\n".join(lines)
