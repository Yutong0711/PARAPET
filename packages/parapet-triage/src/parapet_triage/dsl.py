"""The heuristic linguistic pattern language.

A pattern definition is a disjunction of clauses; a clause is a
conjunction of terms; a term matches a sentence. The published performance
set uses this vocabulary and nothing else:

===========================  ==================================================
``{"a" | "b"}``              any of these phrases appears
``"a"``                      this phrase appears
``X + Y``                    both X and Y appear (in any order)
``X | Y``                    X or Y, when the ``|`` sits outside any brace
``1. X; 2. Y``               X or Y; ``;`` and ``N.`` both start a new clause
``word_contains{"pre"}``     some token contains this substring
``word_contains_"pre"``      same, older spelling
``text_contains{"a b"}``     the substring appears anywhere in the sentence
``contains_"a"``             same
``ner_contains_"PERCENT"``   a named entity of this type is present
``NUMBER``                   a numeral is present
``DURATION``                 a duration is present
``VB`` / ``NN``              a verb / a noun is present
``per_NN_per_NN``            "per <noun> ... per <noun>"
``"x" is noun``              this word appears tagged as a noun
``"a" is before "b"``        both appear, a before b
``two nouns are the same``   a noun is repeated around a joining word
===========================  ==================================================

Robustness matters more than strictness here. Several published
definitions have an unbalanced brace or a missing closing quote, so the
parser recovers what it can and records what it could not; a pattern that
had to be repaired is reported by :func:`compile_set` rather than silently
approximated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

from .text import DURATION_UNITS, MEMORY_UNITS, Sentence

# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------


class Term:
    """One condition on a sentence."""

    kind = "term"

    def matches(self, sentence: Sentence) -> bool:      # pragma: no cover
        raise NotImplementedError

    def describe(self) -> str:                          # pragma: no cover
        raise NotImplementedError

    @property
    def needs_pos(self) -> bool:
        return False


@dataclass
class Phrases(Term):
    """Any of these phrases appears, matched on word boundaries."""

    phrases: Tuple[str, ...]
    kind: str = "phrases"

    def __post_init__(self):
        object.__setattr__(self, "_regex", _phrase_regex(self.phrases))

    def matches(self, sentence: Sentence) -> bool:
        return bool(self._regex.search(sentence.lowered))

    def describe(self) -> str:
        return "{" + " | ".join(f'"{p}"' for p in self.phrases) + "}"


@dataclass
class WordContains(Term):
    """Some token contains one of these substrings."""

    fragments: Tuple[str, ...]
    kind: str = "word_contains"

    def matches(self, sentence: Sentence) -> bool:
        return any(fragment in word
                   for word in sentence.words for fragment in self.fragments)

    def describe(self) -> str:
        return "word_contains{" + " | ".join(self.fragments) + "}"


@dataclass
class TextContains(Term):
    """One of these substrings appears anywhere, word boundaries ignored."""

    fragments: Tuple[str, ...]
    kind: str = "text_contains"

    def matches(self, sentence: Sentence) -> bool:
        lowered = sentence.lowered
        return any(fragment in lowered for fragment in self.fragments)

    def describe(self) -> str:
        return "text_contains{" + " | ".join(self.fragments) + "}"


@dataclass
class EntityType(Term):
    """A named entity of one of these types is present.

    Without a model the sentence's own surface cues stand in: a percent
    sign or the word "percent" for PERCENT, a numeral next to a time unit
    for DURATION. The approximation is why ``backend_report`` lists these
    patterns as degraded on the simple backend.
    """

    types: Tuple[str, ...]
    kind: str = "ner"

    def matches(self, sentence: Sentence) -> bool:
        wanted = {t.upper() for t in self.types}
        if sentence.entity_types() & wanted:
            return True
        if "PERCENT" in wanted and sentence.has_percent():
            return True
        if wanted & {"DURATION", "TIME", "DATE"} and sentence.has_duration():
            return True
        return False

    def describe(self) -> str:
        return "ner{" + " | ".join(self.types) + "}"

    @property
    def needs_pos(self) -> bool:
        return True


@dataclass
class TokenType(Term):
    """A token of this class is present: NUMBER, DURATION, VB or NN."""

    token_type: str
    kind: str = "token_type"

    def matches(self, sentence: Sentence) -> bool:
        name = self.token_type.upper()
        if name == "NUMBER":
            return any(token.is_number for token in sentence.tokens)
        if name == "DURATION":
            return sentence.has_duration()
        if name in ("VB", "VERB"):
            return any(token.pos == "VERB" for token in sentence.tokens)
        if name in ("NN", "NOUN"):
            return any(token.pos == "NOUN" for token in sentence.tokens)
        return False

    def describe(self) -> str:
        return self.token_type.upper()

    @property
    def needs_pos(self) -> bool:
        return self.token_type.upper() in ("VB", "VERB", "NN", "NOUN")


@dataclass
class NumberBeforeUnit(Term):
    """A numeral immediately followed by a duration or memory unit."""

    units: Tuple[str, ...] = tuple(sorted(DURATION_UNITS))
    kind: str = "number_unit"

    def matches(self, sentence: Sentence) -> bool:
        unit_set = set(self.units)
        for index, token in enumerate(sentence.tokens[:-1]):
            if token.is_number and sentence.tokens[index + 1].lower in unit_set:
                return True
        return False

    def describe(self) -> str:
        return "NUMBER+UNIT"


@dataclass
class WordIsPos(Term):
    """One of these words appears with this part of speech."""

    words: Tuple[str, ...]
    pos: str
    kind: str = "word_is_pos"

    def matches(self, sentence: Sentence) -> bool:
        wanted = {w.lower() for w in self.words}
        return any(token.lower in wanted and token.pos == self.pos
                   for token in sentence.tokens)

    def describe(self) -> str:
        return "{" + " | ".join(self.words) + "} is " + self.pos

    @property
    def needs_pos(self) -> bool:
        return True


@dataclass
class Ordered(Term):
    """The first word appears before the second."""

    first: str
    second: str
    kind: str = "ordered"

    def matches(self, sentence: Sentence) -> bool:
        words = sentence.words
        if self.first not in words or self.second not in words:
            return False
        return words.index(self.first) < words.index(self.second)

    def describe(self) -> str:
        return f'"{self.first}" before "{self.second}"'


@dataclass
class RepeatedNoun(Term):
    """A noun repeated around a joining word: "byte by byte", "row by row".

    The paper's own examples all repeat the noun, and matching any
    noun-word-noun triple instead fires on ordinary passives, so repetition
    is required. ``joiners`` is exposed because a pattern set for another
    domain may want a different set.
    """

    joiners: Tuple[str, ...] = ("by", "after", "at", "per", "to")
    kind: str = "repeated_noun"

    def matches(self, sentence: Sentence) -> bool:
        tokens = sentence.tokens
        for index in range(1, len(tokens) - 1):
            if tokens[index].lower not in self.joiners:
                continue
            left, right = tokens[index - 1], tokens[index + 1]
            if left.lower.rstrip("s") and left.lower.rstrip("s") == right.lower.rstrip("s"):
                return True
        return False

    def describe(self) -> str:
        return "noun repeated around " + "/".join(self.joiners)

    @property
    def needs_pos(self) -> bool:
        return True


@dataclass
class PerNounPerNoun(Term):
    """``per <noun> ... per <noun>``: a rate expressed twice over."""

    kind: str = "per_nn_per_nn"

    def matches(self, sentence: Sentence) -> bool:
        positions = [index for index, token in enumerate(sentence.tokens)
                     if token.lower == "per"]
        if len(positions) < 2:
            return False
        followed = [index for index in positions
                    if index + 1 < len(sentence.tokens)
                    and sentence.tokens[index + 1].pos == "NOUN"]
        return len(followed) >= 2

    def describe(self) -> str:
        return "per NN per NN"

    @property
    def needs_pos(self) -> bool:
        return True


@dataclass
class Never(Term):
    """A term that never fires, for a definition nothing could be made of."""

    reason: str = ""
    kind: str = "never"

    def matches(self, sentence: Sentence) -> bool:
        return False

    def describe(self) -> str:
        return f"<never: {self.reason}>"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_QUOTED = re.compile(r'"([^"]*)"')
_CLAUSE_SPLIT = re.compile(r";|(?:(?<=^)|(?<=[\s;}\)]))\d+\.\s*")
_FUNC_BRACE = re.compile(
    r"(word_contains|text_contains|ner_contains|contains)\s*[\{\(]([^\}\)]*)[\}\)]",
    re.I)
_FUNC_UNDERSCORE = re.compile(
    r"(word_contains|text_contains|ner_contains|contains)_\s*"
    r'((?:"[^"]*"(?:\s*\|\s*(?="))?\s*)+)',
    re.I)
_IS_POS = re.compile(r'((?:"[^"]*"\s*\|?\s*)+)\s*is\s+(noun|verb|adj|adv)\b', re.I)
_IS_BEFORE = re.compile(r'"([^"]*)"\s*is\s+before\s+"([^"]*)"', re.I)
_TOKEN_TYPE = re.compile(r"\b(NUMBER|DURATION|VB|NN)\b")

_PROSE_BUILTINS = {
    "per_nn_per_nn": PerNounPerNoun,
    "two nouns are the same": RepeatedNoun,
}

# Bare words the published definitions use as prose rather than as content.
# Applied only to unquoted fragments: a quoted phrase is intentional, even
# when the word inside it is a common one such as "long".
_PROSE_NOISE = re.compile(r"(is|are|the|same|two|nouns|noun|before)", re.I)


@dataclass
class Clause:
    """A conjunction of terms; every term must match."""

    terms: List[Term]

    def matches(self, sentence: Sentence) -> bool:
        return bool(self.terms) and all(term.matches(sentence) for term in self.terms)

    def describe(self) -> str:
        return " + ".join(term.describe() for term in self.terms)


@dataclass
class CompiledPattern:
    """A pattern ready to run, plus how faithfully it compiled."""

    pattern_id: str
    name: str
    category: str
    definition: str
    clauses: List[Clause] = field(default_factory=list)
    repairs: List[str] = field(default_factory=list)

    def matches(self, sentence: Sentence) -> bool:
        return any(clause.matches(sentence) for clause in self.clauses)

    __call__ = matches

    @property
    def needs_pos(self) -> bool:
        return any(term.needs_pos for clause in self.clauses for term in clause.terms)

    @property
    def usable(self) -> bool:
        return any(clause.terms and not isinstance(clause.terms[0], Never)
                   for clause in self.clauses)

    def describe(self) -> str:
        return " OR ".join(f"({clause.describe()})" for clause in self.clauses)


def _phrase_regex(phrases: Sequence[str]) -> "re.Pattern":
    """Word-boundary match for each phrase, with internal spacing relaxed."""
    parts = []
    for phrase in phrases:
        cleaned = phrase.strip().lower()
        if not cleaned:
            continue
        body = r"\s+".join(re.escape(word) for word in cleaned.split())
        left = r"\b" if cleaned[:1].isalnum() else ""
        right = r"\b" if cleaned[-1:].isalnum() else ""
        parts.append(left + body + right)
    if not parts:
        return re.compile(r"(?!x)x")     # matches nothing
    return re.compile("|".join(parts))


def _split_alternatives(blob: str) -> Tuple[str, ...]:
    """Quoted phrases inside a group; bare words when nothing is quoted.

    Quotation marks a phrase as intentional, so a quoted phrase is never
    filtered even when the word inside it is a common one. Only unquoted
    fragments are checked against the prose list.
    """
    quoted = [item.strip() for item in _QUOTED.findall(blob) if item.strip()]
    if quoted:
        return tuple(quoted)
    bare = [item.strip().strip('"{}()') for item in blob.split("|")]
    return tuple(item for item in bare
                 if item and not _PROSE_NOISE.fullmatch(item))


def parse_clause(text: str, repairs: List[str]) -> Clause:
    """Turn one clause into a conjunction of terms.

    Function calls, POS assertions and orderings are pulled out first, so
    the phrases they own are not also read as bare literals. Whatever
    quoted groups remain become ``Phrases`` terms joined by ``+``.
    """
    terms: List[Term] = []
    remaining = text

    for match in _IS_BEFORE.finditer(remaining):
        terms.append(Ordered(match.group(1).lower(), match.group(2).lower()))
    remaining = _IS_BEFORE.sub(" ", remaining)

    for match in _IS_POS.finditer(remaining):
        pos = {"noun": "NOUN", "verb": "VERB", "adj": "ADJ", "adv": "ADV"}[
            match.group(2).lower()]
        terms.append(WordIsPos(_split_alternatives(match.group(1)), pos))
    remaining = _IS_POS.sub(" ", remaining)

    for regex in (_FUNC_BRACE, _FUNC_UNDERSCORE):
        for match in regex.finditer(remaining):
            func = match.group(1).lower()
            fragments = tuple(item.lower() for item in
                              _split_alternatives(match.group(2)))
            if not fragments:
                repairs.append(f"{func}(...) had no readable argument")
                continue
            if func == "word_contains":
                terms.append(WordContains(fragments))
            elif func == "ner_contains":
                terms.append(EntityType(tuple(f.upper() for f in fragments)))
            else:
                terms.append(TextContains(fragments))
        remaining = regex.sub(" ", remaining)

    for match in _TOKEN_TYPE.finditer(remaining):
        terms.append(TokenType(match.group(1)))
    remaining = _TOKEN_TYPE.sub(" ", remaining)

    lowered = remaining.lower()
    for marker, builder in _PROSE_BUILTINS.items():
        if marker in lowered:
            terms.append(builder())
            remaining = re.sub(re.escape(marker), " ", remaining, flags=re.I)

    # Whatever is left: each brace group, or each run of quoted phrases
    # between "+" signs, is one Phrases term.
    for chunk in remaining.split("+"):
        alternatives = _split_alternatives(chunk)
        if alternatives:
            terms.append(Phrases(alternatives))
        elif chunk.strip() and '"' not in chunk and "{" not in chunk:
            stray = chunk.strip().strip(".,;: ")
            if stray and not _PROSE_NOISE.fullmatch(stray):
                repairs.append(f"ignored unquoted fragment {stray!r}")
    return Clause(terms)


_PLACEHOLDER = "\x00{}\x00"

# Two malformed shapes occur in the published set: a phrase that lost its
# opening quote after a "|", and a phrase that lost its closing quote before
# a "}". Repairing them in place keeps every later quote correctly paired,
# which appending a quote at the end does not.
_MISSING_OPEN = re.compile(r'([|{])\s*([A-Za-z][\w /-]*)"')
_MISSING_CLOSE = re.compile(r'"([^"{}|]*?)\}')


def _repair_quotes(definition: str) -> Tuple[str, List[str]]:
    """Balance quotation marks, reporting each repair."""
    repairs: List[str] = []
    if definition.count('"') % 2 == 0:
        return definition, repairs

    repaired, n_open = _MISSING_OPEN.subn(r'\1 "\2"', definition)
    if n_open and repaired.count('"') % 2 == 0:
        repairs.append(f"restored {n_open} missing opening quotation mark(s)")
        return repaired, repairs

    repaired, n_close = _MISSING_CLOSE.subn(r'"\1"}', definition)
    if n_close and repaired.count('"') % 2 == 0:
        repairs.append(f"restored {n_close} missing closing quotation mark(s)")
        return repaired, repairs

    repairs.append("odd number of quotation marks that no repair rule "
                   "matched; the trailing phrase was closed at the end")
    return definition + '"', repairs


def _protect_function_runs(definition: str) -> Tuple[str, Dict[str, str]]:
    """Hide ``func_"a" | "b"`` runs so their ``|`` is not read as a clause break.

    ``word_contains_"kb" | "mb"`` lists alternatives for one function call,
    while ``{"byte"} | word_contains{"-byte"}`` is a disjunction of two
    terms. Both use ``|``; only the second separates clauses.
    """
    saved: Dict[str, str] = {}

    def stash(match):
        key = _PLACEHOLDER.format(len(saved))
        saved[key] = match.group(0)
        return key

    return _FUNC_UNDERSCORE.sub(stash, definition), saved


def _split_top_level(text: str) -> List[str]:
    """Split on ``;``, ``N.`` and any ``|`` outside braces, quotes and parens."""
    pieces, current, depth, in_quote = [], [], 0, False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            in_quote = not in_quote
            current.append(char)
        elif in_quote:
            current.append(char)
        elif char in "{(":
            depth += 1
            current.append(char)
        elif char in "})":
            depth = max(0, depth - 1)
            current.append(char)
        elif depth == 0 and char in ";|":
            pieces.append("".join(current))
            current = []
        elif depth == 0 and char.isdigit():
            # A clause marker is "N." followed by space, at a boundary.
            ahead = re.match(r"\d+\.\s", text[index:])
            before = "".join(current).rstrip()
            if ahead and (not before or before[-1] in ";|}) \x00"):
                pieces.append("".join(current))
                current = []
                index += ahead.end()
                continue
            current.append(char)
        else:
            current.append(char)
        index += 1
    pieces.append("".join(current))
    return [piece for piece in pieces if piece.strip()]


def parse_definition(definition: str, repairs: Optional[List[str]] = None
                     ) -> List[Clause]:
    """Split into clauses on ``;``, ``N.`` and top-level ``|``, then parse."""
    repairs = repairs if repairs is not None else []
    if not definition or not definition.strip():
        return [Clause([Never("empty definition")])]

    definition, quote_repairs = _repair_quotes(definition)
    repairs.extend(quote_repairs)
    opens, closes = definition.count("{"), definition.count("}")
    if opens != closes:
        repairs.append(f"unbalanced braces ({opens} open, {closes} close)")

    protected, saved = _protect_function_runs(definition)
    clauses = []
    for piece in _split_top_level(protected):
        for key, original in saved.items():
            piece = piece.replace(key, original)
        if not piece.strip():
            continue
        clause = parse_clause(piece, repairs)
        if clause.terms:
            clauses.append(clause)
    if not clauses:
        repairs.append("no clause could be parsed")
        return [Clause([Never("unparsed definition")])]
    return clauses


def compile_pattern(spec: Dict[str, str]) -> CompiledPattern:
    """Compile one pattern-set entry."""
    repairs: List[str] = []
    definition = spec.get("definition", "")
    clauses = parse_definition(definition, repairs)
    return CompiledPattern(
        pattern_id=spec.get("id", spec.get("name", "?")),
        name=spec.get("name", "?"),
        category=spec.get("category", "LEX"),
        definition=definition,
        clauses=clauses,
        repairs=repairs)


def compile_set(specs: Sequence[Dict[str, str]]) -> Tuple[List[CompiledPattern], Dict]:
    """Compile a whole set and report how it went.

    The report is the thing to read before trusting a run: it counts the
    patterns that needed repair and the patterns that need a real tagger.
    """
    compiled = [compile_pattern(spec) for spec in specs]
    report = {
        "n_patterns": len(compiled),
        "n_usable": sum(1 for item in compiled if item.usable),
        "n_repaired": sum(1 for item in compiled if item.repairs),
        "n_need_pos": sum(1 for item in compiled if item.needs_pos),
        "repaired": {item.name: item.repairs for item in compiled if item.repairs},
        "unusable": [item.name for item in compiled if not item.usable],
    }
    return compiled, report
