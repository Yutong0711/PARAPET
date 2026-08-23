"""Sentence splitting and token annotation.

Two backends. ``simple`` is the default and needs nothing but the standard
library, so ``pip install parapet-triage`` gives a working classifier. It
covers every pattern that matches on words and phrases, which is most of
them. ``spacy`` adds part-of-speech tags and named entities, which six of
the eighty performance patterns need; without it those six degrade to a
lexical approximation and :func:`backend_report` says which.

That split is deliberate. A tool a maintainer cannot install in an hour is
a tool a maintainer does not install.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

_SENTENCE = re.compile(r"(?<=[.!?])[\s\n]+|\n{2,}")
_WORD = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*|\d+(?:[.,]\d+)?")

# Units that let the simple backend approximate CoreNLP's DURATION entity.
DURATION_UNITS = {
    "ns", "nanosecond", "nanoseconds", "us", "microsecond", "microseconds",
    "ms", "msec", "millisecond", "milliseconds", "s", "sec", "secs", "second",
    "seconds", "m", "min", "mins", "minute", "minutes", "h", "hr", "hrs",
    "hour", "hours", "day", "days", "week", "weeks", "month", "months",
}
MEMORY_UNITS = {"b", "kb", "kib", "mb", "mib", "gb", "gib", "tb", "tib",
                "byte", "bytes", "kilobyte", "megabyte", "gigabyte"}

# Suffix rules good enough to decide "is this token a noun / a verb" for the
# handful of patterns that ask. Not a tagger; see backend_report().
_VERB_SUFFIX = ("ing", "ed", "ate", "ize", "ise", "ify")
_NOUN_SUFFIX = ("tion", "sion", "ment", "ness", "ity", "ance", "ence", "ship",
                "er", "or", "ism", "age")


@dataclass
class Token:
    text: str
    lower: str
    index: int
    pos: str = ""          # coarse: NOUN VERB ADJ ADV NUM other
    tag: str = ""          # Penn tag when a real tagger ran
    ent_type: str = ""
    lemma: str = ""

    @property
    def is_number(self) -> bool:
        return self.pos == "NUM" or self.tag == "CD" or \
            bool(re.fullmatch(r"\d+(?:[.,]\d+)?", self.text))


@dataclass
class Sentence:
    """One annotated sentence plus the surface text the patterns scan."""

    text: str
    tokens: List[Token] = field(default_factory=list)
    issue_key: str = ""
    position: int = 0
    backend: str = "simple"

    @property
    def lowered(self) -> str:
        """Lower-cased text with runs of whitespace collapsed.

        Phrase patterns match against this, so ``"speed up"`` finds
        ``"Speed\\n  up"`` the way a reader would.
        """
        if not hasattr(self, "_lowered"):
            object.__setattr__(self, "_lowered", re.sub(r"\s+", " ", self.text).lower())
        return self._lowered

    @property
    def words(self) -> List[str]:
        return [token.lower for token in self.tokens]

    def entity_types(self) -> Set[str]:
        return {token.ent_type for token in self.tokens if token.ent_type}

    def has_percent(self) -> bool:
        return "%" in self.text or "PERCENT" in self.entity_types() \
            or any(word in {"percent", "percentage"} for word in self.words)

    def has_duration(self) -> bool:
        if self.entity_types() & {"TIME", "DATE", "DURATION"}:
            return True
        for index, token in enumerate(self.tokens[:-1]):
            if token.is_number and self.tokens[index + 1].lower in DURATION_UNITS:
                return True
        return False

    def nouns(self) -> List[Token]:
        return [token for token in self.tokens if token.pos == "NOUN"]


class SimpleBackend:
    """Regex tokeniser with suffix-based part-of-speech guesses."""

    name = "simple"
    has_pos = False
    has_ner = False

    _FUNCTION_WORDS = {
        "the", "a", "an", "of", "to", "in", "on", "for", "with", "at", "by",
        "from", "as", "is", "are", "was", "were", "be", "been", "being", "and",
        "or", "but", "if", "then", "than", "that", "this", "these", "those",
        "it", "its", "we", "you", "they", "he", "she", "not", "no", "so",
        "when", "while", "which", "who", "what", "how", "there", "here",
    }

    def split(self, text: str) -> List[str]:
        parts = [part.strip() for part in _SENTENCE.split(text or "")]
        return [part for part in parts if part]

    def _pos(self, word: str) -> str:
        low = word.lower()
        if re.fullmatch(r"\d+(?:[.,]\d+)?", word):
            return "NUM"
        if low in self._FUNCTION_WORDS:
            return "FUNC"
        if low.endswith(_NOUN_SUFFIX):
            return "NOUN"
        if low.endswith(_VERB_SUFFIX):
            return "VERB"
        if low.endswith(("ly",)):
            return "ADV"
        if low.endswith(("ous", "ive", "ful", "less", "able", "ible", "al")):
            return "ADJ"
        return "NOUN"

    def annotate(self, text: str) -> Sentence:
        tokens = []
        for index, match in enumerate(_WORD.finditer(text or "")):
            word = match.group(0)
            pos = self._pos(word)
            tokens.append(Token(text=word, lower=word.lower(), index=index,
                                pos=pos, lemma=_naive_lemma(word)))
        return Sentence(text=text, tokens=tokens, backend=self.name)


class SpacyBackend:
    """spaCy for part of speech and named entities."""

    name = "spacy"
    has_pos = True
    has_ner = True

    _POS_MAP = {"NOUN": "NOUN", "PROPN": "NOUN", "VERB": "VERB", "AUX": "VERB",
                "ADJ": "ADJ", "ADV": "ADV", "NUM": "NUM"}

    def __init__(self, model: str = "en_core_web_sm"):
        try:
            import spacy
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "spaCy is not installed. Either `pip install "
                "'parapet-triage[nlp]' && python -m spacy download "
                "en_core_web_sm`, or use the default simple backend.") from exc
        try:
            self.nlp = spacy.load(model, disable=["lemmatizer"])
        except OSError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                f"spaCy model {model!r} is missing. Run "
                f"`python -m spacy download {model}`.") from exc

    def split(self, text: str) -> List[str]:
        return [sent.text.strip() for sent in self.nlp(text or "").sents
                if sent.text.strip()]

    def annotate(self, text: str) -> Sentence:
        doc = self.nlp(text or "")
        tokens = []
        for index, token in enumerate(t for t in doc if not t.is_space):
            tokens.append(Token(
                text=token.text, lower=token.text.lower(), index=index,
                pos=self._POS_MAP.get(token.pos_, token.pos_),
                tag=token.tag_, ent_type=token.ent_type_,
                lemma=token.lemma_.lower()))
        return Sentence(text=text, tokens=tokens, backend=self.name)


def _naive_lemma(word: str) -> str:
    low = word.lower()
    for suffix, replacement in (("ies", "y"), ("sses", "ss"), ("es", ""), ("s", "")):
        if low.endswith(suffix) and len(low) > len(suffix) + 2:
            return low[: len(low) - len(suffix)] + replacement
    return low


@lru_cache(maxsize=4)
def get_backend(name: str = "simple", model: str = "en_core_web_sm"):
    if name == "simple":
        return SimpleBackend()
    if name == "spacy":
        return SpacyBackend(model)
    raise ValueError(f"unknown backend {name!r}; expected 'simple' or 'spacy'")


def split_sentences(text: str, backend=None) -> List[Sentence]:
    backend = backend or get_backend()
    out = []
    for position, raw in enumerate(backend.split(text)):
        sentence = backend.annotate(raw)
        sentence.position = position
        out.append(sentence)
    return out


def backend_report(backend) -> Dict[str, object]:
    """What the current backend can and cannot decide.

    Printed by ``parapet-triage doctor`` so a degraded run is visible
    before its numbers are believed rather than after.
    """
    return {
        "backend": backend.name,
        "part_of_speech": "tagger" if backend.has_pos else "suffix heuristic",
        "named_entities": "model" if backend.has_ner else "unit lists",
        "degraded_patterns": [] if backend.has_pos and backend.has_ner else [
            "per", "nn_by_nn", "load_NN", "fast", "percentage", "duration"],
    }
