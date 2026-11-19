# SPDX-License-Identifier: Apache-2.0
"""Pre-registered rule for turning a raw model response into a patch (claim L1).

The raw response is saved verbatim BEFORE this runs. Extraction never edits
code: it selects text that is already in the response.

Rule, applied in order:

1. Take the first closed fenced code block (```...```) whose body declares
   ``class <TargetSimpleName>``. The body is used exactly as written.
2. Otherwise, if the response contains no fenced block at all, starts like a
   Java compilation unit (``package``, ``import``, a comment, or a class
   modifier) and declares the class, use the whole response.
3. Otherwise there is no parseable patch.

The extracted text replaces the whole target file.
"""

from __future__ import annotations

import re

FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_+.-]*)[^\n]*\n(.*?)```", re.S)
JAVA_START = re.compile(r"^(package|import|/\*|//|public|final|class|@)")


def extract_java(text: str | None, class_name: str) -> tuple[str | None, str]:
    if not text:
        return None, "empty response"
    decl = re.compile(rf"\bclass\s+{re.escape(class_name)}\b")
    blocks = FENCE.findall(text)
    for i, (lang, body) in enumerate(blocks):
        if decl.search(body):
            tag = lang or "no language tag"
            return body, f"fenced code block #{i + 1} ({tag}) declaring class {class_name}"
    stripped = text.strip()
    if not blocks and decl.search(stripped) and JAVA_START.match(stripped):
        return stripped + "\n", f"whole response (no fenced block) declaring class {class_name}"
    if blocks:
        return None, f"{len(blocks)} fenced block(s), none declares class {class_name}"
    if "```" in text:
        return None, "unclosed code fence (response may be truncated)"
    return None, f"no fenced code block and no class {class_name} declaration"
