"""The record every PARAPET component reads and writes.

A hardening record says four things about one proposed change: what it
removes, the check that proves it, what it cost, and how to reproduce
both. Every component fills part of it, and the parts compose because they
share this schema.

The record is the security-critical artifact of the system. Anything that
can bend it can move a change through review without touching the code, so
every field that a reader would rely on is hashed, and every record carries
the version of the tool and the environment that produced it.
"""

from .schema import (RECORD_SCHEMA_VERSION, Budget, BudgetCheck, CostMeasure,
                     Exposure, HardeningRecord, Provenance, ReviewCost,
                     ToolResult)
from .provenance import (content_digest, environment_profile, file_digest,
                         new_provenance)
from .io import load_record, merge_results, save_record

__all__ = [
    "RECORD_SCHEMA_VERSION", "Budget", "BudgetCheck", "CostMeasure",
    "Exposure", "HardeningRecord", "Provenance", "ReviewCost", "ToolResult",
    "content_digest", "environment_profile", "file_digest", "new_provenance",
    "load_record", "merge_results", "save_record",
]
__version__ = "0.1.0"
