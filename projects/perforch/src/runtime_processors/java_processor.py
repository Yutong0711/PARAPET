from . import core

def wrap_java(full_code, iterations):
    code = full_code.split("\n")
    main_start = -1
    main_end = -1
    brace_count = 0

    for i, line in enumerate(code):
        if "public static void main(String[] args)" in line:
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
    loop_code = [
        f"{indent}{indent}for (int warp = 0; warp < {iterations}; warp++) {{\n"
    ]
    loop_code += [indent + line for line in code[main_start + 1 : main_end]]
    loop_code.append(f"{indent}{indent}}}\n")
    modified_code = code[: main_start + 1] + loop_code + code[main_end:]
    return "\n".join(modified_code)


correctness_test, refine_test = core.build_processor_api(
    source_relpath="Main.java",
    wrap_fn=wrap_java,
    compile_fn="javac Main.java",
    run_cmd="java Main",
    memory_cmd="java Main",
)
