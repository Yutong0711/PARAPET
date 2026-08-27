
from typing import Dict, List
import json
import gzip


class BenchmarkLoader:
    def __init__(self, benchmark_name: str, language: str, base_dir: str = "benchmark"):
        """
        Loads a benchmark dataset into memory and builds a task_id index.
        """
        benchmark = benchmark_name.lower()
        language_lower = language.lower()
        if benchmark == "effibenchx":
            json_path = f"{base_dir}/effibenchx/effibenchx-{language_lower}.jsonl.gz"
        elif benchmark == "humanevalpack":
            json_path = f"{base_dir}/humanevalpack/humanevalpack-{language_lower}.jsonl"
        else:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")

        self.json_path = json_path
        self.filename = json_path.split("/")[-1].split(".")[0]
        self.benchmark_name = benchmark

        self.data = self._load_data()
        self._task_id_index = {p.get("task_id"): p for p in self.data if p.get("task_id")}

    def _load_data(self) -> List[Dict]:
        data = []
        if self.json_path.endswith(".jsonl.gz"):
            with gzip.open(self.json_path, "rt", encoding="utf-8") as file:
                for line in file:
                    data.append(json.loads(line.strip()))
        else:
            with open(self.json_path, "r", encoding="utf-8") as file:
                if self.json_path.endswith(".jsonl"):
                    for line in file:
                        data.append(json.loads(line.strip()))
                else:
                    data = json.load(file)
        return data

    def get_problem_by_task_id(self, task_id: str) -> Dict:
        problem = self._task_id_index.get(task_id)
        if problem:
            return problem
        raise ValueError(f"Problem with task_id {task_id} not found.")
