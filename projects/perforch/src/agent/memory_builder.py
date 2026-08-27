import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock


def _atomic_write_json(path: str, data: list[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp_path, path)


def _normalize_record(record: dict, stage: str = "") -> dict:
    base = {
        "task_id": record.get("task_id", ""),
        "model": record.get("model", ""),
        "stage": record.get("stage", stage),
        "LLM_input": record.get("LLM_input", ""),
        "LLM_output": record.get("LLM_output", ""),
        "function_before": record.get("function_before", None),
        "function_after": record.get("function_after", ""),
        "passed": bool(record.get("passed", False)),
    }
    if base["stage"] == "refine" or "before" in record:
        base["before"] = record.get("before") or {}
        base["after"] = record.get("after") or {}
    return base


def _process_one(
    stage: str, benchmark: str, language: str, problem_data: dict, model_name: str,
    temperature: float = None, top_p: float = None,
) -> dict | None:
    from codegen.full_code_generator import generate_full_code
    from codegen.function_extractor import extract_function_by_language
    from agent.workflow_ops import evaluate_candidate, run_llm_function_op

    task_id = problem_data["task_id"]
    try:
        if stage == "generate":
            llm_res = run_llm_function_op(problem_data, language, model_name, "generate", temperature=temperature, top_p=top_p)
            function_before = None
        else:
            buggy_body = problem_data.get("buggy_solution", "")
            llm_res = run_llm_function_op(
                problem_data, language, model_name, "fix",
                input_function_code=buggy_body,
                temperature=temperature,
                top_p=top_p,
            )
            raw = problem_data.get("declaration", "") + buggy_body
            function_before = extract_function_by_language(
                language, raw, problem_data.get("entry_point", "")
            )
        function_after = llm_res.get("function_after", "") or ""
        full_code = generate_full_code(problem_data, language, function_after, benchmark)
        correctness = evaluate_candidate(language, task_id, full_code, test_type="correctness")
        passed = bool(correctness.get("passed"))
        return {
            "task_id": task_id,
            "model": model_name,
            "stage": stage,
            "LLM_input": llm_res.get("LLM_input", "") or "",
            "LLM_output": llm_res.get("LLM_output", "") or "",
            "function_before": function_before,
            "function_after": function_after,
            "passed": passed,
        }
    except Exception as e:
        print(f"Skip invalid record: {task_id} | {model_name} | {e.__class__.__name__}: {str(e)}")
        return None


def _process_one_refine(
    benchmark: str, language: str, problem_data: dict, model_name: str
) -> dict | None:
    from codegen.full_code_generator import generate_full_code
    from codegen.function_extractor import extract_function_by_language
    from agent.workflow_ops import evaluate_candidate, run_llm_function_op

    task_id = problem_data["task_id"]
    try:
        canonical = problem_data.get("canonical_solution", "")
        full_code = generate_full_code(problem_data, language, canonical, benchmark)
        before = evaluate_candidate(language, task_id, full_code, test_type="full", benchmark=benchmark)
        if not before.get("passed"):
            print(f"Skip refine (original failed profile): {task_id} | {model_name}")
            return None

        llm_res = run_llm_function_op(
            problem_data, language, model_name, "refine",
            input_function_code=canonical, overhead_analysis=before,
        )
        function_after = llm_res.get("function_after", "") or ""
        refined_full = generate_full_code(problem_data, language, function_after, benchmark)
        after = evaluate_candidate(language, task_id, refined_full, test_type="full", benchmark=benchmark)

        raw = problem_data.get("declaration", "") + canonical
        function_before = extract_function_by_language(
            language, raw, problem_data.get("entry_point", "")
        )
        return {
            "task_id": task_id,
            "model": model_name,
            "stage": "refine",
            "LLM_input": llm_res.get("LLM_input", "") or "",
            "LLM_output": llm_res.get("LLM_output", "") or "",
            "function_before": function_before,
            "function_after": function_after,
            "before": before,
            "after": after,
            "passed": bool(after.get("passed")),
        }
    except Exception as e:
        print(f"Skip invalid record: {task_id} | {model_name} | {e.__class__.__name__}: {str(e)}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build memory files (generate, fix, or refine) for AgentMemory model ranking."
    )
    parser.add_argument(
        "--stage",
        default="generate",
        choices=["generate", "fix", "refine"],
        help="Stage to build memory for: 'generate', 'fix', or 'refine'.",
    )
    parser.add_argument(
        "--benchmark",
        default="humanevalpack",
        choices=["humanevalpack"],
        help="Benchmark to initialize from (currently only humanevalpack).",
    )
    parser.add_argument(
        "--languages",
        default="cpp,go,java,python,rust",
        help="Comma-separated languages to include.",
    )
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated model names configured in src/config/api_config.py.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Target memory file path (default: data/memory/memory.json).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker threads for API + correctness runs.",
    )
    parser.add_argument(
        "--flush-every",
        type=int,
        default=5,
        help="Flush output every N completed records (default: 5).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing output and regenerate selected (task_id, model) entries.",
    )
    parser.add_argument(
        "--limit-per-language",
        type=int,
        default=0,
        help="Debug option: only process first N tasks per language (0 means all).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="LLM sampling temperature. Default: use model default (typically 1.0).",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="LLM top-p (nucleus sampling). Default: use model default.",
    )
    args = parser.parse_args()
    if not args.output:
        args.output = "data/memory/memory.json"

    # Lazy imports keep "--help" usable even if runtime deps are missing.
    from benchmark_loader import BenchmarkLoader

    languages = [x.strip().lower() for x in args.languages.split(",") if x.strip()]
    models = [x.strip() for x in args.models.split(",") if x.strip()]
    if not languages:
        raise SystemExit("No languages specified.")
    if not models:
        raise SystemExit("No models specified.")
    if args.workers <= 0:
        raise SystemExit("--workers must be >= 1")
    if args.flush_every <= 0:
        raise SystemExit("--flush-every must be >= 1")
    if args.limit_per_language < 0:
        raise SystemExit("--limit-per-language must be >= 0")

    records: list[dict] = []
    index_by_key: dict[tuple[str, str, str], int] = {}
    resume_enabled = not args.no_resume

    if resume_enabled and os.path.exists(args.output) and os.path.getsize(args.output) > 0:
        with open(args.output, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, list):
            raise SystemExit(f"Output JSON must be a list: {args.output}")
        for item in loaded:
            if not isinstance(item, dict):
                continue
            normalized = _normalize_record(item, stage=args.stage)
            key = (normalized["task_id"], normalized["model"], normalized["stage"])
            index_by_key[key] = len(records)
            records.append(normalized)

    stage = args.stage
    tasks: list[tuple[str, dict, str]] = []
    for language in languages:
        loader = BenchmarkLoader(args.benchmark, language)
        problems = loader.data
        if args.limit_per_language > 0:
            problems = problems[: args.limit_per_language]
        for problem_data in problems:
            task_id = problem_data.get("task_id")
            if not task_id:
                continue
            if stage == "fix" and not problem_data.get("buggy_solution", "").strip():
                continue
            if stage == "refine" and not problem_data.get("canonical_solution", "").strip():
                continue
            for model in models:
                key = (task_id, model, stage)
                if resume_enabled and key in index_by_key:
                    continue
                tasks.append((language, problem_data, model))

    total_planned = len(tasks)
    print(
        f"Planned new records: {total_planned} "
        f"(languages={languages}, models={models}, resume={resume_enabled})"
    )
    if total_planned == 0:
        _atomic_write_json(args.output, records)
        print(f"Nothing to run. Existing records kept: {len(records)}")
        return

    completed = 0
    passed_count = 0
    failed_count = 0
    skipped_invalid_count = 0
    write_lock = Lock()

    def upsert_record(record: dict) -> None:
        key = (record["task_id"], record["model"], record["stage"])
        if key in index_by_key:
            records[index_by_key[key]] = record
        else:
            index_by_key[key] = len(records)
            records.append(record)

    def handle_result(rec: dict | None, task_id: str, model: str) -> None:
        nonlocal completed, passed_count, failed_count, skipped_invalid_count
        completed += 1
        if rec is None:
            skipped_invalid_count += 1
            print(f"[{completed}/{total_planned}] {task_id} | {model} | skipped_invalid=True")
        else:
            upsert_record(rec)
            if rec["passed"]:
                passed_count += 1
            else:
                failed_count += 1
            print(
                f"[{completed}/{total_planned}] {rec['task_id']} | {rec['model']} | "
                f"passed={rec['passed']}"
            )
        if completed % args.flush_every == 0 or completed == total_planned:
            _atomic_write_json(args.output, records)

    def _dispatch(language, problem_data, model):
        if stage == "refine":
            return _process_one_refine(args.benchmark, language, problem_data, model)
        return _process_one(stage, args.benchmark, language, problem_data, model, temperature=args.temperature, top_p=args.top_p)

    if args.workers == 1:
        for language, problem_data, model in tasks:
            rec = _dispatch(language, problem_data, model)
            handle_result(rec, problem_data["task_id"], model)
    else:
        futures = {}
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            for language, problem_data, model in tasks:
                fut = ex.submit(_dispatch, language, problem_data, model)
                futures[fut] = (problem_data["task_id"], model)
            for fut in as_completed(futures):
                task_id, model = futures[fut]
                rec = fut.result()
                with write_lock:
                    handle_result(rec, task_id, model)

    records.sort(key=lambda x: (x.get("task_id", ""), x.get("model", ""), x.get("stage", "")))
    _atomic_write_json(args.output, records)

    print(
        f"Done. attempted={total_planned}, skipped_invalid={skipped_invalid_count}, "
        f"new_passed={passed_count}, new_failed={failed_count}, total_records={len(records)}"
    )
    print(f"Saved memory file to {args.output}")


if __name__ == "__main__":
    main()
