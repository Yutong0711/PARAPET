import os
import threading
import tempfile
import shutil
from .core import run_with_timeout
from . import core

def wrap_rs(full_code, iterations):
    code = full_code.split("\n")
    main_start = -1
    main_end = -1
    brace_count = 0
    modified_code = []

    for i, line in enumerate(code):
        if "fn main()" in line:
            main_start = i
            brace_count = 1
            modified_code.append(line)
        elif main_start != -1:
            if "{" in line:
                brace_count += line.count("{")
            if "}" in line:
                brace_count -= line.count("}")
            
            if brace_count == 0:
                main_end = i
                break
            
            if main_start + 1 == i:  # First line after "fn main()"
                indent = " " * (len(line) - len(line.lstrip()))
                modified_code.append(f"{indent}for _warp in 0..{iterations} {{\n")
                modified_code.append(f"{indent}{indent}{line.lstrip()}")
            else:
                modified_code.append(f"{indent}{line}")
        else:
            modified_code.append(line)

    if main_start == -1 or main_end == -1:
        raise ValueError("No valid main function found.")

    modified_code.append(f"{indent}}}\n")
    modified_code.extend(code[main_end:])
    return "\n".join(modified_code)


def compile_rs(temp_dir, timeout):
    cargo_home = os.path.join(
        tempfile.gettempdir(),
        f"cargo_cache_{os.getpid()}_{threading.current_thread().ident}",
    )
    os.makedirs(cargo_home, exist_ok=True)
    try:
        env = os.environ.copy()
        env["CARGO_HOME"] = cargo_home

        run_output = run_with_timeout("cargo clean", timeout, temp_dir, env=env)
        run_output = run_with_timeout("cargo build", timeout, temp_dir, env=env)

        return True, run_output
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(cargo_home, ignore_errors=True)

correctness_test, refine_test = core.build_processor_api(
    source_relpath=os.path.join("src", "main.rs"),
    wrap_fn=wrap_rs,
    compile_fn=compile_rs,
    run_cmd="target/debug/rust",
    memory_cmd="target/debug/rust",
)
