import json
import math
import os

BENCHMARK_CATEGORY_FILES = {
    "humanevalpack": "benchmark/humanevalpack/humanevalpack-category.json",
    "effibenchx": "benchmark/effibenchx/effibenchx-category.json",
}

DEFAULT_AVAILABLE_MODELS = [
    "GithubCopilot",
    "TONGYILingma",
    "GeminiCodingAssistant",
    "claude_3_7_sonnet_20250219",
    "grok3",
]


def load_category_file(path: str) -> dict | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def lookup_categories_by_id(task_id: str, benchmark_name: str | None = None) -> list | None:
    """Look up category tags for a task_id from benchmark category files."""
    id_str = task_id.split("/", 1)[-1] if "/" in task_id else task_id
    benchmark = benchmark_name.lower() if benchmark_name else None

    if benchmark:
        path = BENCHMARK_CATEGORY_FILES.get(benchmark)
        if path:
            data = load_category_file(path)
            if data and id_str in data:
                return data[id_str]

    for path in BENCHMARK_CATEGORY_FILES.values():
        data = load_category_file(path)
        if data and id_str in data:
            return data[id_str]

    return None


def compute_improvement(before: dict, after: dict, metric: str) -> float | None:
    """Compute relative improvement for a metric between before/after dicts.

    Returns positive values when the metric improved (decreased for time/memory,
    increased for cpus_utilized). Returns None if values are missing or invalid.
    """
    b = before.get(metric)
    a = after.get(metric)
    if b is None or a is None:
        return None
    try:
        b = float(b)
        a = float(a)
    except (TypeError, ValueError):
        return None
    if b == 0:
        return None
    if metric == "cpus_utilized":
        return (a - b) / b
    return (b - a) / b


def atomic_write_json(path: str, data, *, sanitize_floats: bool = False) -> None:
    """Write JSON atomically via tmp+rename. Optionally sanitize non-finite floats."""
    def _sanitize(value):
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, list):
            return [_sanitize(v) for v in value]
        if isinstance(value, dict):
            return {k: _sanitize(v) for k, v in value.items()}
        return value

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp_path = f"{path}.tmp"
    payload = _sanitize(data) if sanitize_floats else data
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=not sanitize_floats)
        f.write("\n")
    os.replace(tmp_path, path)
