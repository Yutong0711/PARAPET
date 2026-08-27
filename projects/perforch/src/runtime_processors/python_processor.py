import sys
from . import core

PYTHON_BIN = sys.executable

def wrap_py(full_code, iterations):
    code = full_code.split("\n")
    # Prefer wrapping the test cases block if present.
    marker = "# Test cases"
    try:
        marker_idx = next(i for i, line in enumerate(code) if line.strip().startswith(marker))
        loop_line = f"for warp in range({iterations}):"
        wrapped = code[: marker_idx + 1] + [loop_line]
        for line in code[marker_idx + 1 :]:
            if line.strip() == "":
                wrapped.append(line)
            else:
                wrapped.append("    " + line)
        return "\n".join(wrapped)
    except StopIteration:
        pass

    # Fallback: wrap the first top-level check(...) call if present.
    wrapped = []
    loop_inserted = False
    indent = ""
    for line in code:
        stripped = line.strip()
        if stripped.startswith("check("):
            if not loop_inserted:
                indent = line[: len(line) - len(line.lstrip())]
                wrapped.append(f"{indent}for warp in range({iterations}):")
                loop_inserted = True
            wrapped.append(indent + "    " + stripped)
        else:
            wrapped.append(line)
    if loop_inserted:
        return "\n".join(wrapped)

    return full_code

correctness_test, refine_test = core.build_processor_api(
    source_relpath="main.py",
    wrap_fn=wrap_py,
    compile_fn=None,
    run_cmd=f"{PYTHON_BIN} main.py",
    memory_cmd=f"{PYTHON_BIN} main.py",
)
