"""parapet: turn an exposure into a reviewable decision.

The three components each answer one question. This package chains them so
a maintainer runs one command and gets one document.

    parapet run --repo . --commit HEAD \\
        --issues issues.csv \\
        --before before.csv --after after.csv \\
        --budget parapet-budget.yaml \\
        --out records/

What comes back is a hardening record: what the change is about, how wide
it is and how to review it, what it cost, where that cost landed, and
whether it fits the budget the project declared in advance.

Every component is optional. Run with only ``--issues`` and you get
triage; add ``--commit`` and you get review cost; add profiles and you get
measured cost and attribution; add a budget and you get a verdict.
"""

from .budget import load_budget, write_budget_template
from .pipeline import PipelineResult, run_pipeline

__all__ = ["run_pipeline", "PipelineResult", "load_budget",
           "write_budget_template"]
__version__ = "0.1.0"
