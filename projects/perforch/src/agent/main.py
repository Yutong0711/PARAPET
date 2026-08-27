from __future__ import annotations


def agent(
    *,
    benchmark_name: str,
    language: str = "Python",
    problem_id: str,
    top_n: int = 5,
    refine_mode: str = "first_improvement",
    metric: str = "execution_time",
    batch_mode: bool = False,
    available_models: list[str] | None = None,
):
    """
    Run the end-to-end PerfOrch pipeline for a single task.

    Prefer `python -m agent.main ...` for CLI usage.
    """
    from .memory import AgentMemory
    from .pipeline import PerfOrchPipeline

    memory = AgentMemory(available_models=available_models, auto_load=True)
    pipeline = PerfOrchPipeline(memory, benchmark_name, language)

    result = pipeline.run_pipeline(
        problem_id=problem_id,
        top_n=top_n,
        refine_mode=refine_mode,
        metric=metric,
        batch_mode=batch_mode,
    )
    print(f"Pipeline Result for {problem_id}: {result.get('status')}")
    return result


def main() -> None:
    import argparse
    import json
    import sys

    from .memory import AgentMemory
    from .pipeline import PerfOrchPipeline

    p = argparse.ArgumentParser(
        prog="python -m agent.main",
        description="Run the PerfOrch end-to-end pipeline for a single task.",
    )
    p.add_argument("--benchmark", required=True, choices=["humanevalpack", "effibenchx"])
    p.add_argument("--language", required=True, help="Language name, e.g. Python/Go/Java/Rust/CPP.")
    p.add_argument("--problem-id", required=True, help="Task id in the form Language/ID, e.g. Python/1.")
    p.add_argument("--top-n", type=int, default=5)
    p.add_argument("--metric", default="execution_time")
    p.add_argument("--refine-mode", default="first_improvement", choices=["first_improvement", "best_of_n"])
    p.add_argument("--batch-mode", action="store_true", help="Skip performance profiling; only check correctness.")
    p.add_argument(
        "--available-models",
        default="",
        help="Comma-separated model allowlist. If set, memory.get_top_models will only return these models.",
    )
    args = p.parse_args()

    available_models = None
    if args.available_models.strip():
        available_models = [m.strip() for m in args.available_models.split(",") if m.strip()]

    memory = AgentMemory(available_models=available_models, auto_load=True)
    pipeline = PerfOrchPipeline(memory, args.benchmark, args.language)
    result = pipeline.run_pipeline(
        problem_id=args.problem_id,
        top_n=args.top_n,
        refine_mode=args.refine_mode,
        metric=args.metric,
        batch_mode=args.batch_mode,
    )

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

