from . import core

def wrap_cpp(full_code, iterations):
    code = full_code.split("\n")
    main_start = -1
    main_end = -1
    brace_count = 0
    return_line = None

    for i, line in enumerate(code):
        if "int main" in line:
            main_start = i
            brace_count = 0
        if main_start != -1:
            brace_count += line.count("{")
            brace_count -= line.count("}")
            if brace_count == 0 and main_start != -1 and main_end == -1:
                main_end = i
                break

    if main_start == -1 or main_end == -1:
        raise ValueError("No valid main function found.")

    indent = "    "
    body_lines = code[main_start + 1 : main_end]
    for line in body_lines:
        if line.strip().startswith("return "):
            return_line = line
            break

    loop_code = [f"{indent}for (int warp = 0; warp < {iterations}; warp++) {{\n"]
    for line in body_lines:
        if return_line is not None and line == return_line:
            continue
        loop_code.append(indent + line)
    loop_code.append(f"{indent}}}\n")
    if return_line is not None:
        loop_code.append(indent + return_line)
    modified_code = code[: main_start + 1] + loop_code + code[main_end:]
    return "\n".join(modified_code)

correctness_test, refine_test = core.build_processor_api(
    source_relpath="main.cpp",
    wrap_fn=wrap_cpp,
    compile_fn="g++ -std=c++20 -o main main.cpp -lssl -lcrypto",
    run_cmd="./main",
    memory_cmd="./main",
)
