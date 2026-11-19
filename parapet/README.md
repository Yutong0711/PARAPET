# `parapet/` — the hardening workflow (1.1.0-alpha)

Apache-2.0. For one known weakness: **Generate** candidate fixes with a local
open-weight model, **Validate** that each passes the checks registered for the
case and keeps required behavior, **Measure** what it costs on the project's own workload,
**Decide** which fit a budget declared in advance. Output: a decision and a
hardening record per patch.

```bash
# hand-written patches only (no model)
python -m parapet run --case C1 --no-generator \
  --budget parapet/budgets/strict.parapet.budget.yaml \
  --budget parapet/budgets/lenient.parapet.budget.yaml
# with the default local generator (Ollama on 127.0.0.1:11434)
python -m parapet run --case C1 \
  --budget parapet/budgets/strict.parapet.budget.yaml \
  --budget parapet/budgets/lenient.parapet.budget.yaml
```

| Module | Stage |
| --- | --- |
| `budget.py` | load and validate `parapet.budget.yaml` (strict and lenient profiles in `budgets/`) |
| `generate.py`, `prompt.py`, `extract.py` | k candidates through PerfOrch's `llm_generator.generate_text`; frozen prompt (`prompts/harden_v1.txt`); verbatim raw outputs; extraction rule |
| `validate.py` | compile, reproducer, two held-out variants, functional tests, probes — each in its own JVM |
| `measure.py`, `stats.py` | forked JVMs per arm, interleaved, warm-up discarded, raw samples; ratio of medians with 95% bootstrap CI; A/A noise floor |
| `decide.py` | fit = upper CI bound at or below each cap; recommend lowest latency upper bound |
| `record.py` | hardening record, JSON + Markdown |
| `cli.py` | `python -m parapet run --case C1 --budget <file>` |

Pre-registered settings: `settings/measurement.yaml`,
`settings/generation.yaml`, `settings/decision_rule.yaml`. Cases:
`cases/C1` (CWE-502), `cases/C2` (CWE-611), and `cases/L1` (java-xmlbuilder,
CWE-611, a real library at a historical commit). Reference and control patches live
under `cases/*/reference/`, outside the `src/` directory the prompt builder
reads.

PerfOrch (`projects/perforch`) is reused by import only; nothing under
`projects/` is modified.
