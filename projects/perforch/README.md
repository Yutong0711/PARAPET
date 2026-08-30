# PerfOrch

> **Vendored snapshot.** Source: https://github.com/qzydustin/perforch @ `e873cd9` (fetched 2026-08-28).
> Code lives in [`src/`](src/). The `data/` directory of benchmark result JSONs
> (EffiBenchX / HumanEvalPack across five model families, ~16 MB) was removed —
> clone upstream for the full result set. Project-level content here is released
> under the [Apache License 2.0](LICENSE) by decision of the project team.
>
> **PARAPET-maintained change.** This snapshot is not byte-identical to upstream:
> it carries one portability fix, in
> [`src/runtime_processors/core.py`](src/runtime_processors/core.py) and
> [`src/runtime_processors/python_processor.py`](src/runtime_processors/python_processor.py),
> so the runtime launches candidates through an argv list instead of a shell
> command string. Without it the Python backend cannot run at all from a checkout
> whose path contains a space. The fix is **not** present at the pinned commit
> `e873cd9`, and whether upstream has since made an equivalent change has not been
> verified here. Nothing else in the snapshot was modified, and no measurement,
> benchmark, or code-generation behavior was changed.

PerfOrch is an LLM-agent pipeline for performance-aware code generation and
runtime measurement. It generates candidate implementations, extracts and
compiles functions across multiple languages, executes them, and records
execution time and memory against benchmark suites (EffiBenchX, HumanEvalPack).

Within **PARAPET** it is the seed pipeline: it already runs "generate candidates
→ measure on real workloads," the middle of the hardening loop that PARAPET
wraps with a security objective and a declared cost budget.

## Layout

- `src/agent/` — classifier, memory / memory-builder, pipeline, and workflow orchestration.
- `src/codegen/` — full-program and function-level code generation, function extraction, prompt building.
- `src/runtime_processors/` — per-language compile-and-run backends (C++, Go, Java, Python, Rust) and a registry.
- `src/benchmark_loader.py` — benchmark ingestion.
- `src/llm_generator.py` — model invocation.
- `src/config/` — API configuration.
