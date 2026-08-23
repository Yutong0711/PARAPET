"""parapet-triage: route issue reports and advisories by what they describe.

The tool decides one thing: does this report describe the kind of problem
you are looking for. It decides it with named linguistic patterns rather
than an opaque model, so every verdict comes with the patterns that
produced it and a maintainer can check the reasoning in a few seconds.

    from parapet_triage import Triager

    triager = Triager()                       # the 80 performance patterns
    verdict = triager.classify_text(
        "The parser is slow: a 4 MB file takes 30 seconds to load.")
    print(verdict.label, verdict.patterns)
    print(verdict.explain())

Two pattern sets ship with the package. ``performance`` is the published,
corpus-validated set of 80. ``security`` is a starter set for hardening
work, in the same format, and has not been validated; see its header.
Write your own with ``load_pattern_set("my-set.yaml")``.
"""

from .classify import (DEFAULT_ISSUE_THRESHOLD, DEFAULT_SENTENCE_THRESHOLD,
                       IssueVerdict, LearnedScorer, SentenceVerdict, Triager)
from .dsl import CompiledPattern, compile_pattern, compile_set, parse_definition
from .patterns import BUILTIN_SETS, PatternSet, load_pattern_set, save_pattern_set
from .sources import Report, load_reports
from .text import Sentence, backend_report, get_backend, split_sentences

__all__ = [
    "Triager", "IssueVerdict", "SentenceVerdict", "LearnedScorer",
    "DEFAULT_ISSUE_THRESHOLD", "DEFAULT_SENTENCE_THRESHOLD",
    "CompiledPattern", "compile_pattern", "compile_set", "parse_definition",
    "PatternSet", "BUILTIN_SETS", "load_pattern_set", "save_pattern_set",
    "Report", "load_reports",
    "Sentence", "get_backend", "split_sentences", "backend_report",
]
__version__ = "0.1.0"
