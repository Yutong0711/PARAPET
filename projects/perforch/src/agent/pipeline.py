import logging
from typing import List, Dict

from .classifier import classify_problem
from .memory import AgentMemory
from .utils import compute_improvement
from .workflow_ops import run_llm_function_op, evaluate_candidate
from codegen.full_code_generator import generate_full_code
from benchmark_loader import BenchmarkLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration Constants
DEFAULT_GENERATE_FIX_ATTEMPTS = 5
DEFAULT_CLASSIFY_MODEL = "GithubCopilot"

class PerfOrchPipeline:
    def __init__(self, memory: AgentMemory, benchmark_name: str, language: str):
        self.memory = memory
        self.benchmark_name = benchmark_name
        self.language = language
        self.benchmark = self._load_benchmark()

    def _load_benchmark(self) -> BenchmarkLoader:
        """Load benchmark data based on name and language."""
        language_lower = self.language.lower()
        return BenchmarkLoader(self.benchmark_name, language_lower)

    def run_pipeline(
        self, 
        problem_id: str, 
        top_n: int = 5, 
        refine_mode: str = "first_improvement", 
        metric: str = "execution_time", 
        batch_mode: bool = False
    ) -> Dict:
        """
        Executes the end-to-end pipeline for a single problem.
        """
        problem_data = self.benchmark.get_problem_by_task_id(problem_id)
        if not problem_data:
            logging.error(f"Problem {problem_id} not found.")
            return {"status": "error", "message": "Problem not found"}
            
        logging.info(f"Starting pipeline for problem: {problem_id}")
        
        # 1. Classification
        classification_res = self._classify_step(problem_data)
        tags = classification_res.get("tags", [])
        logging.info(f"Classified tags: {tags}")
        
        # 2. Model Selection
        models = self._model_selection_step(tags, top_n, metric)
        logging.info(f"Selected models: Generate: {models['generate']}, Fix: {models['fix']}, Refine: {models['refine']}")
        
        # 3. Generate & Fix Loop
        gen_fix_result = self._generate_fix_step(problem_data, models['generate'], models['fix'])
        
        if not gen_fix_result['passed']:
            logging.info("Generate and Fix failed.")
            return {
                "status": "failed",
                "stage": "generate_fix",
                "result": gen_fix_result
            }
            
        logging.info(f"Generate/Fix passed with code from {gen_fix_result['model']}")
        current_code = gen_fix_result['code']
        
        # 4. Refine Loop
        refine_result = self._refine_step(
            problem_data, 
            current_code, 
            models['refine'], 
            refine_mode, 
            metric, 
            batch_mode=batch_mode
        )
        
        return {
            "status": "success",
            "final_code": refine_result.get('refined_code') or current_code,
            "refined": refine_result['refined'],
            "improvement": refine_result.get('improvement', 0),
            "classification_details": classification_res,
            "generate_fix_details": gen_fix_result,
            "refine_details": refine_result
        }

    def _classify_step(self, problem_data: Dict) -> Dict:
        """Classify the problem using LLM."""
        description = problem_data.get("prompt", "") # Using prompt as description
        task_id = problem_data.get("task_id", "")
        # We don't have solution yet, so pass empty or handle in classifier
        # Classifier already updated to handle optional solution
        result = classify_problem(
            description,
            DEFAULT_CLASSIFY_MODEL,
            benchmark_task_id=task_id,
            benchmark_name=self.benchmark_name
        )
        return result

    def _model_selection_step(self, tags: List[str], top_n: int, metric: str) -> Dict[str, List[str]]:
        """Select top models for generate, fix, and refine using AgentMemory."""
        return {
            "generate": self.memory.get_top_models(self.language, tags, "generate", top_n),
            "fix": self.memory.get_top_models(self.language, tags, "fix", top_n),
            # For refine, metric is needed. Assuming execution_time as default or passed metric
            "refine": self.memory.get_top_models(self.language, tags, "refine", top_n, metric=metric) 
        }

    def _generate_fix_step(self, problem_data: Dict, generate_models: List[str], fix_models: List[str]) -> Dict:
        """
        Try to generate correct code. If fails, try to fix.
        Loop: Generate Model i -> Test -> (If Fail) Fix Model 1..N -> Test -> (If Fail) Next Gen Model
        """
        history = []
        
        for gen_idx, gen_model in enumerate(generate_models):
            logging.info(f"Generating with model {gen_model} ({gen_idx+1}/{len(generate_models)})")
            
            # Generate
            gen_result = run_llm_function_op(problem_data, self.language, gen_model, "generate")
            code = gen_result.get("function_after", "")
            
            # Test
            full_code = generate_full_code(problem_data, self.language, code, self.benchmark_name)
            test_res = evaluate_candidate(self.language, problem_data["task_id"], full_code, test_type="correctness")
            
            history.append({
                "stage": "generate", 
                "model": gen_model, 
                "passed": test_res["passed"],
                "code": code,
                "LLM_input": gen_result.get("LLM_input"),
                "LLM_output": gen_result.get("LLM_output"),
                "full_code": full_code,
                "test_result_raw": test_res
            })
            
            if test_res["passed"]:
                return {"passed": True, "code": code, "model": gen_model, "stage": "generate", "history": history}
            
            # If generation failed, try fixing (only when fix models are provided)
            if not fix_models:
                continue
            logging.info("Generation failed, attempting fixes...")
            for fix_idx, fix_model in enumerate(fix_models):
                logging.info(f"Fixing with model {fix_model} ({fix_idx+1}/{len(fix_models)})")
                
                fix_result = run_llm_function_op(problem_data, self.language, fix_model, "fix", input_function_code=code)
                fixed_code = fix_result.get("function_after", "")
                
                # Test Fix
                fix_full_code = generate_full_code(problem_data, self.language, fixed_code, self.benchmark_name)
                fix_test_res = evaluate_candidate(self.language, problem_data["task_id"], fix_full_code, test_type="correctness")
                
                history.append({
                    "stage": "fix", 
                    "model": fix_model, 
                    "base_gen_model": gen_model,
                    "passed": fix_test_res["passed"],
                    "code": fixed_code,
                    "LLM_input": fix_result.get("LLM_input"),
                    "LLM_output": fix_result.get("LLM_output"),
                    "full_code": fix_full_code,
                    "test_result_raw": fix_test_res
                })
                
                if fix_test_res["passed"]:
                     return {"passed": True, "code": fixed_code, "model": fix_model, "stage": "fix", "fixed_from": gen_model, "history": history}
            
            # If all fixes failed, continue to next generate model
            logging.info("All fixes failed for this generation.")

        return {"passed": False, "history": history}

    def _refine_step(
        self,
        problem_data: Dict,
        original_code: str,
        refine_models: List[str],
        refine_mode: str,
        metric: str,
        batch_mode: bool = False
    ) -> Dict:
        """
        Refine the code for performance.
        In batch_mode, it only generates refined codes and tests correctness, skipping performance profiling.
        """
        logging.info(f"Starting refinement. Mode: {refine_mode}, Metric: {metric}, Batch Mode: {batch_mode}")
        
        # 1. Profile Original Code
        if not batch_mode:
            logging.info("Profiling original code...")
            gen_full_code = generate_full_code(problem_data, self.language, original_code, self.benchmark_name)
            original_profile = evaluate_candidate(self.language, problem_data["task_id"], gen_full_code, test_type="full", benchmark=self.benchmark_name)
            
            if not original_profile.get("passed"):
                 logging.warning("Original code failed during full profiling (unexpected as it passed correctness check).")
                 return {"refined": False, "reason": "original_failed_profile", "original_metrics": original_profile}
                 
            overhead_analysis = original_profile
        else:
            logging.info("Batch mode: Skipping original code profiling.")
            original_profile = {"passed": True}
            overhead_analysis = {}
        
        best_refined_code = None
        best_improvement = 0
        best_model = None
        
        history = []
        
        for model in refine_models:
            logging.info(f"Refining with model {model}...")
            
            # Refine
            refine_result = run_llm_function_op(
                problem_data, 
                self.language, 
                model, 
                "refine", 
                input_function_code=original_code,
                overhead_analysis=overhead_analysis
            )
            refined_code = refine_result.get("function_after", "")
            
            # Test Correctness First
            ref_full_code = generate_full_code(problem_data, self.language, refined_code, self.benchmark_name)
            correctness_res = evaluate_candidate(self.language, problem_data["task_id"], ref_full_code, test_type="correctness")
            
            if not correctness_res["passed"]:
                logging.info(f"Refined code by {model} failed correctness test.")
                history.append({
                    "model": model, 
                    "passed_correctness": False,
                    "LLM_input": refine_result.get("LLM_input"),
                    "LLM_output": refine_result.get("LLM_output"),
                    "test_result_raw": correctness_res
                })
                continue
            
            if batch_mode:
                logging.info(f"Refined code by {model} passed correctness. Saving for offline verification.")
                history.append({
                    "model": model,
                    "passed_correctness": True,
                    "refined_code": refined_code,
                    "LLM_input": refine_result.get("LLM_input"),
                    "LLM_output": refine_result.get("LLM_output"),
                    "test_result_raw": correctness_res
                })
                # In batch mode, we continue to generate all top N models
                continue

            # Test Performance (Only if NOT in batch mode)
            logging.info(f"Refined code by {model} passed correctness. Profiling performance...")
            profile_res = evaluate_candidate(self.language, problem_data["task_id"], ref_full_code, test_type="full", benchmark=self.benchmark_name)

            improvement = compute_improvement(original_profile, profile_res, metric) or 0.0
            
            logging.info(f"Model {model} improvement: {improvement:.2%}")
            
            history.append({
                "model": model, 
                "passed_correctness": True, 
                "metrics": profile_res, 
                "improvement": improvement,
                "LLM_input": refine_result.get("LLM_input"),
                "LLM_output": refine_result.get("LLM_output"),
                "test_result_raw": profile_res
            })
            
            is_better = improvement > 0 # Can add threshold logic if needed
            
            if is_better:
                if refine_mode == "first_improvement":
                    return {
                        "refined": True,
                        "refined_code": refined_code,
                        "model": model,
                        "improvement": improvement,
                        "original_metrics": original_profile,
                        "refined_metrics": profile_res,
                        "history": history
                    }
                elif refine_mode == "best_of_n":
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_refined_code = refined_code
                        best_model = model
        
        if batch_mode:
             return {
                "refined": False, # Status is not yet known
                "batch_generated": True,
                "history": history
            }

        if best_refined_code:
             return {
                "refined": True,
                "refined_code": best_refined_code,
                "model": best_model,
                "improvement": best_improvement,
                "original_metrics": original_profile,
                "history": history # Note: 'refined_metrics' would be in history for best model
            }
            
        return {
            "refined": False, 
            "reason": "no_improvement_found", 
            "original_metrics": original_profile,
            "history": history
        }
