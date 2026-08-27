# PerfOrch

> **Vendored snapshot.** Source: https://github.com/qzydustin/perforch @ `e873cd9` (fetched 2026-08-28).
> Code lives in [`src/`](src/). The `data/` directory of benchmark result JSONs
> (EffiBenchX / HumanEvalPack across five model families, ~16 MB) was removed —
> clone upstream for the full result set.

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
