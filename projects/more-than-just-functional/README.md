> **Vendored snapshot.** From the *PESOSE — Derui Zhu Prior Research Code Artifacts* bundle (v1.0, 2026-08-23),
> `research_artifacts/more-than-just-functional`. Paper: "More Than Just Functional: LLM-as-a-Critique for
> Efficient Code Generation," NeurIPS 2025. Code lives in [`src/`](src/). Project-level content here is
> released under the [Apache License 2.0](LICENSE) by decision of the project team.
> Background evidence only — no performance deliverable is claimed for PARAPET.

# Fastdecoder
An optimized n-best strategies for high time and memory efficiency code generation

## First Step: Generate Python Codes for the tasks with:
```code
python src/code_generation_for_task.py
```

## Second Step: add memory and time profiler to the generated py code with:
```code
python add_profiler_to_py_code.py
```

## Third Step: Calculate the Time Efficiency for each python code with corresponding profiler:
```code
#for time efficiency calculation
python time_efficiency_profile.py

#for memory efficiency calculation
python memory_efficiency_profile.py
```

## Fourth Step: Collect the profile report and generate the final statistical results:
```code
python read_dat_to_generate_final_result.py
``` 
