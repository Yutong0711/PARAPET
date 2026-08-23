"""Turning pattern matches into a decision about an issue.

Three levels, following the framework this package implements:

1. Pattern tagging turns a sentence into a vector of pattern hits.
2. Sentence scoring turns that vector into "is this sentence about the
   topic".
3. Issue scoring aggregates the sentences of one report into a verdict.

The default scorer is a transparent weighted sum, not a trained model.
That is a deliberate trade. A trained model scores a little better and
cannot tell a maintainer *why* an issue was routed to them; a weighted sum
over named patterns can, and for a tool whose output feeds a security
review, being able to say "this fired because it matched
``negative_necessary`` and ``spend_time``" is worth more than a point of
F1. :class:`LearnedScorer` is available for anyone who disagrees.

Weights come from the per-pattern precision published with the pattern
set. A pattern that was right 99% of the time counts for more than one
that was right 85% of the time, and no fitting is involved, so the
classifier behaves identically on every machine.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .dsl import CompiledPattern, compile_set
from .patterns import PatternSet, load_pattern_set
from .text import Sentence, get_backend, split_sentences

# One confident pattern is enough. Every set a user writes is unweighted,
# because ``precision`` is optional, so if an unweighted hit cannot reach
# the sentence threshold then such a set can never fire on a single
# pattern, and the "write your own pattern set" path is silently broken.
# These three are coupled: keep DEFAULT_WEIGHT at or above the sentence
# threshold, and the issue threshold at or below it, so one matching
# sentence carries an issue. ``test_an_unweighted_pattern_can_match_alone``
# pins the relation.
DEFAULT_SENTENCE_THRESHOLD = 0.90
DEFAULT_ISSUE_THRESHOLD = 0.90
DEFAULT_WEIGHT = DEFAULT_SENTENCE_THRESHOLD


@dataclass
class SentenceVerdict:
    """One sentence, the patterns it matched, and the score they earn."""

    text: str
    position: int
    patterns: List[str] = field(default_factory=list)
    score: float = 0.0
    is_match: bool = False

    def to_dict(self) -> dict:
        return {"position": self.position, "text": self.text,
                "patterns": list(self.patterns), "score": round(self.score, 4),
                "is_match": self.is_match}


@dataclass
class IssueVerdict:
    """The decision for one issue report, with the evidence behind it."""

    identifier: str
    label: str                       # match | no-match
    score: float
    confidence: float
    patterns: List[str] = field(default_factory=list)
    sentences: List[SentenceVerdict] = field(default_factory=list)
    set_id: str = ""
    backend: str = "simple"

    @property
    def is_match(self) -> bool:
        return self.label == "match"

    @property
    def matching_sentences(self) -> List[SentenceVerdict]:
        return [item for item in self.sentences if item.is_match]

    def explain(self, limit: int = 3) -> str:
        """Why this verdict, in one paragraph a maintainer can check."""
        if not self.is_match:
            return (f"{self.identifier}: no match. No sentence scored above "
                    f"the threshold; {len(self.sentences)} sentence(s) were "
                    "examined.")
        lines = [f"{self.identifier}: match (score {self.score:.2f}, "
                 f"confidence {self.confidence:.2f}). Patterns: "
                 f"{', '.join(self.patterns[:8])}."]
        for item in self.matching_sentences[:limit]:
            snippet = item.text if len(item.text) <= 160 else item.text[:157] + "..."
            lines.append(f"  [{'+'.join(item.patterns[:3])}] {snippet}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {"identifier": self.identifier, "label": self.label,
                "score": round(self.score, 4),
                "confidence": round(self.confidence, 4),
                "patterns": list(self.patterns), "set_id": self.set_id,
                "backend": self.backend,
                "sentences": [item.to_dict() for item in self.sentences]}


class Triager:
    """Classify issue reports against a pattern set.

    ``weights`` maps a pattern name to how much a hit counts. When a
    pattern set ships published per-pattern precision, that is used;
    otherwise every pattern counts :data:`DEFAULT_WEIGHT`.
    """

    def __init__(self,
                 pattern_set: Optional[PatternSet] = None,
                 weights: Optional[Dict[str, float]] = None,
                 backend: str = "simple",
                 spacy_model: str = "en_core_web_sm",
                 sentence_threshold: float = DEFAULT_SENTENCE_THRESHOLD,
                 issue_threshold: float = DEFAULT_ISSUE_THRESHOLD):
        self.pattern_set = pattern_set or load_pattern_set("performance")
        self.patterns, self.compile_report = compile_set(self.pattern_set.patterns)
        self.weights = dict(weights or _weights_from_set(self.pattern_set))
        self.backend = get_backend(backend, spacy_model)
        self.sentence_threshold = sentence_threshold
        self.issue_threshold = issue_threshold

    # -- level 1 ---------------------------------------------------------
    def tag_sentence(self, sentence: Sentence) -> List[str]:
        """Names of the patterns that match; the paper's Sentence HLP Vector."""
        return [pattern.name for pattern in self.patterns if pattern.matches(sentence)]

    def vector(self, sentence: Sentence) -> List[int]:
        return [1 if pattern.matches(sentence) else 0 for pattern in self.patterns]

    # -- level 2 ---------------------------------------------------------
    def score_sentence(self, sentence: Sentence) -> SentenceVerdict:
        names = self.tag_sentence(sentence)
        score = sum(self.weights.get(name, DEFAULT_WEIGHT) for name in names)
        return SentenceVerdict(text=sentence.text, position=sentence.position,
                               patterns=names, score=score,
                               is_match=score >= self.sentence_threshold)

    # -- level 3 ---------------------------------------------------------
    def classify_text(self, text: str, identifier: str = "") -> IssueVerdict:
        """Classify one report from its title and body as a single string."""
        sentences = split_sentences(text or "", self.backend)
        verdicts = [self.score_sentence(sentence) for sentence in sentences]
        matched = [item for item in verdicts if item.is_match]

        # An issue scores as the strongest sentence plus a diminishing bonus
        # for corroboration. One decisive sentence should be enough, and ten
        # weak ones should not add up to the same thing.
        best = max((item.score for item in verdicts), default=0.0)
        extra = sum(item.score for item in matched) - best
        score = best + math.log1p(max(0.0, extra))

        names: List[str] = []
        for item in matched or verdicts:
            for name in item.patterns:
                if name not in names:
                    names.append(name)
        label = "match" if score >= self.issue_threshold else "no-match"
        return IssueVerdict(
            identifier=identifier, label=label, score=score,
            confidence=_confidence(score, self.issue_threshold),
            patterns=names, sentences=verdicts,
            set_id=self.pattern_set.set_id, backend=self.backend.name)

    def classify_many(self, items: Iterable[Tuple[str, str]]) -> List[IssueVerdict]:
        """``(identifier, text)`` pairs in, verdicts out."""
        return [self.classify_text(text, identifier) for identifier, text in items]

    def report(self) -> dict:
        """What this triager is, for the provenance block of a record."""
        return {"set_id": self.pattern_set.set_id,
                "n_patterns": len(self.patterns),
                "backend": self.backend.name,
                "sentence_threshold": self.sentence_threshold,
                "issue_threshold": self.issue_threshold,
                **{key: self.compile_report[key]
                   for key in ("n_usable", "n_repaired", "n_need_pos")}}


def _confidence(score: float, threshold: float) -> float:
    """Squash the distance from the threshold into ``[0, 1]``.

    This is a readable monotone transform of the score, not a calibrated
    probability, and it is named ``confidence`` because that is what a
    reader will take it for. Do not threshold decisions on it a second
    time.
    """
    return 1.0 / (1.0 + math.exp(-(score - threshold)))


def _weights_from_set(pattern_set: PatternSet) -> Dict[str, float]:
    """Per-pattern weights, from published precision when the set has it."""
    weights = {}
    for item in pattern_set.patterns:
        value = item.get("precision")
        weights[item["name"]] = float(value) if value is not None else DEFAULT_WEIGHT
    return weights


class LearnedScorer:
    """Optional trained level-2/level-3 classifier over the pattern vector.

    Needs scikit-learn, and needs labelled sentences. It exists so the
    transparent scorer can be checked against a fitted one on your own
    data; it is not what ``parapet-triage classify`` uses by default.
    """

    def __init__(self, triager: Triager, model: str = "logistic", seed: int = 42):
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "LearnedScorer needs scikit-learn: "
                "pip install 'parapet-triage[learn]'") from exc
        self.triager = triager
        self.model = (LogisticRegression(max_iter=1000, class_weight="balanced",
                                         random_state=seed)
                      if model == "logistic"
                      else RandomForestClassifier(n_estimators=200, n_jobs=-1,
                                                  class_weight="balanced",
                                                  random_state=seed))

    def _design(self, texts: Sequence[str]):
        import numpy as np
        rows = [self.triager.vector(self.triager.backend.annotate(text))
                for text in texts]
        return np.asarray(rows, dtype=float)

    def fit(self, texts: Sequence[str], labels: Sequence[int]) -> "LearnedScorer":
        self.model.fit(self._design(texts), list(labels))
        return self

    def predict(self, texts: Sequence[str]):
        return self.model.predict(self._design(texts))

    def feature_importance(self) -> List[Tuple[str, float]]:
        """Pattern names ranked by the fitted model's own weights."""
        import numpy as np
        if hasattr(self.model, "coef_"):
            values = np.asarray(self.model.coef_).ravel()
        elif hasattr(self.model, "feature_importances_"):
            values = np.asarray(self.model.feature_importances_)
        else:  # pragma: no cover - defensive
            return []
        names = [pattern.name for pattern in self.triager.patterns]
        return sorted(zip(names, values.tolist()), key=lambda kv: -abs(kv[1]))
