import json

from .utils import BENCHMARK_CATEGORY_FILES, lookup_categories_by_id, compute_improvement, load_category_file

full_model = [
    "CodeQwen1.5_7B_Chat", "Llama_3.2_3B_Instruct", "Llama_3.1_8B_Instruct",
    "gemma_2_9b_it", "Qwen2.5_14B_Instruct", "Phi_3_medium_128k_instruct",
    "GithubCopilot", "TONGYILingma", "BaiduComate", "CodeGeeX",
    "GeminiCodingAssistant", "claude_3_7_sonnet_20250219", "codestral_mamba_2407", "grok3"
]
MEMORY_FILE = "data/memory/memory.json"
THRESHOLD_FILE = "data/memory/threshold.json"


class AgentMemory:
    def __init__(self, available_models: list[str] | None = None, *, auto_load: bool = False):
        self.generate_data = {}
        self.fix_data = {}
        self.refine_data = {}
        # Copy to avoid accidental global mutation of `full_model`.
        self.available_models = list(available_models) if available_models is not None else list(full_model)
        self._category_maps = self._load_category_maps()
        self._thresholds = self._load_thresholds()
        # Cache: (model_type, metric, language, tags_tuple, is_refine) -> {model: score}
        self._score_cache: dict[tuple, dict] = {}
        if auto_load:
            self.load_data()

    def _load_category_maps(self) -> dict:
        maps = {}
        for name, path in BENCHMARK_CATEGORY_FILES.items():
            maps[name] = load_category_file(path) or {}
        return maps
    
    def _load_thresholds(self) -> dict:
        try:
            with open(THRESHOLD_FILE, "r") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _get_tags_for_task(self, task_id: str) -> list:
        if not task_id:
            return ["Unknown"]
        result = lookup_categories_by_id(task_id)
        return result if result else ["Unknown"]

    def _get_language_for_task(self, task_id: str) -> str:
        if not task_id:
            return "unknown"
        return task_id.split("/", 1)[0].lower() if "/" in task_id else "unknown"

    def _compute_improvement(self, before: dict, after: dict, metric: str) -> float | None:
        return compute_improvement(before, after, metric)
        
    def load_data(self):
        """Load model performance data from unified memory.json file."""
        # Allow reloading without double-counting.
        self.generate_data = {}
        self.fix_data = {}
        self.refine_data = {}
        self._score_cache.clear()
        # Reload thresholds in case the file changed.
        self._thresholds = self._load_thresholds()

        try:
            with open(MEMORY_FILE, 'r') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            print(f"Warning: {MEMORY_FILE} not found")
            return
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {MEMORY_FILE}")
            return

        if not isinstance(all_data, list):
            raise TypeError(f"Memory data must be list, got {type(all_data).__name__} in {MEMORY_FILE}")

        # Group records by stage
        stage_groups = {"generate": [], "fix": [], "refine": []}
        for item in all_data:
            if not isinstance(item, dict):
                continue
            stage = item.get("stage", "")
            if stage in stage_groups:
                stage_groups[stage].append(item)

        # Process each stage
        for stage, records in stage_groups.items():
            target_dict = getattr(self, f"{stage}_data")
            self._process_list_data(records, target_dict, stage)
    
    def _process_list_data(self, data, target_dict, data_type: str):
        """Process list-structured memory logs and build flattened indexes."""
        if data_type in {"generate", "fix"}:
            counts = {}
            for item in data:
                task_id = item.get("task_id", "")
                model = item.get("model", "")
                if not model:
                    continue
                language = self._get_language_for_task(task_id)
                tags = self._get_tags_for_task(task_id)
                passed = bool(item.get("passed"))
                for tag in tags:
                    key = (language, tag, model)
                    if key not in counts:
                        counts[key] = {"passed": 0, "total": 0}
                    counts[key]["total"] += 1
                    if passed:
                        counts[key]["passed"] += 1

            for (language, tag, model), stat in counts.items():
                metric = "pass_rate"
                dict_key = f"{language}-{tag}-{metric}"
                if dict_key not in target_dict:
                    target_dict[dict_key] = {}
                total = stat["total"]
                pass_rate = (stat["passed"] / total) if total else 0.0
                target_dict[dict_key][model] = {"pass_rate": pass_rate}
            return

        if data_type == "refine":
            # Expect cleaned refine logs: list of {task_id, model, before, after}.
            # We aggregate per (language, tag, metric, model):
            # - ensure the model is present in that bucket if improvement is computable (imp is not None)
            # - accumulate only imp > threshold > 0 into sum_improvements
            metrics = ("execution_time", "max_memory", "average_memory", "cpus_utilized")

            # Hot-path caches: task_id repeats across many models; avoid repeated parsing and tag lookups.
            lang_cache: dict[str, str] = {}
            tags_cache: dict[str, list[str]] = {}

            # Pre-normalize thresholds for fast lookups: (language, metric) -> float
            thr_cache: dict[tuple[str, str], float] = {}

            for item in data:
                task_id = item.get("task_id") or ""
                model = item.get("model") or ""
                if not task_id or not model:
                    continue

                before = item.get("before") or {}
                after = item.get("after") or {}
                if not isinstance(before, dict) or not isinstance(after, dict):
                    continue
                if not after.get("passed"):
                    continue

                language = lang_cache.get(task_id)
                if language is None:
                    language = self._get_language_for_task(task_id)
                    lang_cache[task_id] = language

                tags = tags_cache.get(task_id)
                if tags is None:
                    tags = self._get_tags_for_task(task_id)
                    tags_cache[task_id] = tags

                for metric in metrics:
                    imp = self._compute_improvement(before, after, metric)
                    if imp is None:
                        continue

                    # Ensure bucket+model exists as long as improvement is computable.
                    # This matches the previous behavior that kept zero-sum models for tie-breaking.
                    for tag in tags:
                        dict_key = f"{language}-{tag}-{metric}"
                        bucket = target_dict.setdefault(dict_key, {})
                        model_entry = bucket.get(model)
                        if model_entry is None:
                            bucket[model] = {"sum_improvements": 0.0}

                        if imp <= 0:
                            continue

                        thr_key = (language, metric)
                        thr = thr_cache.get(thr_key)
                        if thr is None:
                            thr = float(self._thresholds.get(metric, {}).get(language, 0.0))
                            thr_cache[thr_key] = thr

                        if imp <= thr:
                            continue

                        # Safe: model key exists because we created it above.
                        bucket[model]["sum_improvements"] += float(imp)
            return
    
    def _calculate_model_scores(self, language: str, tag: list[str], data_dict: dict, metric: str, is_refine: bool = False):
        """Compute aggregated model scores across multiple tags."""
        model_scores = {}
        
        for single_tag in tag:
            data_key = f"{language}-{single_tag}-{metric}"
            if data_key not in data_dict:
                print(f"Warning: {data_key} not found")
                continue

            for model, data in data_dict[data_key].items():
                if model not in model_scores:
                    model_scores[model] = 0.0 if is_refine else 1.0

                if is_refine:
                    model_scores[model] += data.get('sum_improvements', 0)
                else:
                    model_scores[model] *= data.get('pass_rate', 0)
        
        return model_scores

    def _get_cached_scores(self, language: str, tag: list[str], model_type: str, metric: str, is_refine: bool) -> dict:
        language = language.lower()
        tag_key = tuple(sorted(tag))
        cache_key = (model_type, metric, language, tag_key, is_refine)
        cached = self._score_cache.get(cache_key)
        if cached is not None:
            return cached
        data_dict = getattr(self, f"{model_type}_data", None)
        if data_dict is None:
            scores = {}
        else:
            scores = self._calculate_model_scores(language, list(tag_key), data_dict, metric, is_refine)
        self._score_cache[cache_key] = scores
        return scores
    
    def get_top_models(self, language: str, tag: list[str], model_type: str, num_models: int, metric: str = "pass_rate"):
        """Return top-N models for a given language and tag set.
        
        Args:
            language: Programming language (case-insensitive).
            tag: List of tags (categories).
            model_type: One of {"generate", "fix", "refine"}.
            num_models: Number of models to return.
            metric: Scoring metric. For generate/fix it's "pass_rate". For refine, use a refine metric
                like "execution_time", "max_memory", "average_memory", or "cpus_utilized".
        """
        # 获取对应的数据字典
        data_dict = getattr(self, f"{model_type}_data", None)
        if data_dict is None:
            print(f"Warning: {model_type} data not found")
            return []
        
        # 计算模型分数
        language = language.lower()
        is_refine = (model_type == "refine")
        model_scores = self._get_cached_scores(language, tag, model_type, metric, is_refine)
        if not model_scores:
            return []

        # Tie-break rules:
        # - refine: primary=sum_improvements; if equal, prefer higher fix pass_rate, then generate pass_rate; then name.
        # - others: primary=pass_rate; if equal, then name.
        if is_refine:
            fix_pass = self._get_cached_scores(language, tag, "fix", "pass_rate", is_refine=False)
            gen_pass = self._get_cached_scores(language, tag, "generate", "pass_rate", is_refine=False)

            def sort_key(m: str) -> tuple:
                return (
                    -float(model_scores.get(m, 0.0)),
                    -float(fix_pass.get(m, 0.0)),
                    -float(gen_pass.get(m, 0.0)),
                    m,
                )

            ordered = sorted(model_scores.keys(), key=sort_key)
        else:
            ordered = sorted(model_scores.keys(), key=lambda m: (-float(model_scores.get(m, 0.0)), m))

        available_models = [m for m in ordered if m in self.available_models][:num_models]
        
        # 返回结果：始终返回列表格式
        return available_models 
