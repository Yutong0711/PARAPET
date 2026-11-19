# SPDX-License-Identifier: Apache-2.0
"""The frozen hardening prompt.

The prompt carries exactly two inputs: the vulnerable source file and the
weakness class (CWE id and name). It never reads a reference fix, the control
patch, the harness (reproducer, held-out variants, tests), or any model
output: the builder opens one file, the case target, and nothing else.
"""

from __future__ import annotations

from parapet.case import Case
from parapet.hashing import sha256_text
from parapet.paths import PROMPTS_DIR

TEMPLATE_NAME = "harden_v1.txt"


def template_text(name: str = TEMPLATE_NAME) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def build_prompt(case: Case, template_name: str = TEMPLATE_NAME) -> str:
    template = template_text(template_name)
    source = case.read_target()
    return (
        template.replace("{cwe_id}", case.cwe_id)
        .replace("{cwe_name}", case.cwe_name)
        .replace("{file_path}", case.target_relpath)
        .replace("{source}", source.rstrip("\n"))
    )


def prompt_record(case: Case, template_name: str = TEMPLATE_NAME) -> dict:
    text = build_prompt(case, template_name)
    return {
        "template": f"parapet/prompts/{template_name}",
        "template_sha256": sha256_text(template_text(template_name)),
        "prompt_sha256": sha256_text(text),
        "inputs": {
            "source_file": str(case.target_path.relative_to(case.dir.parent.parent.parent)),
            "cwe_id": case.cwe_id,
            "cwe_name": case.cwe_name,
        },
    }
