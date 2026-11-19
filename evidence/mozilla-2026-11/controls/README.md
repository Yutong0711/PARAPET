# Hosted control (Step 5) — not run

Purpose of the step: attribution only (does model-induced cost or failure come
from the local generator or from the prompt and cases?). It is not part of
PARAPET's default path.

Status: **skipped**. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` were both unset
in the session environment (presence checked at about 16:38 PST and at
18:30:58 PST on 2026-11-18; no value was read or printed). No hosted model
was called and no hosted endpoint was contacted, so there is no hosted
endpoint log. `parapet/generate.py` refuses any non-loopback generator unless
`--allow-hosted-control` is passed.
