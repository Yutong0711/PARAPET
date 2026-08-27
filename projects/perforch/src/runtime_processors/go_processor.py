from . import core

def wrap_go(full_code, iterations):
    code = full_code.split("\n")
    modified_code = []
    i = 0
    while i < len(code):
        line = code[i]
        if line.strip().startswith("func Test"):
            modified_code.append(line)
            i += 1
            brace_count = 1
            indent = "\t"
            function_body = []
            while i < len(code) and brace_count > 0:
                brace_count += code[i].count("{")
                brace_count -= code[i].count("}")
                function_body.append(code[i])
                i += 1
            modified_code.append(
                f"{indent}for warp := 0; warp < {iterations}; warp++ {{\n"
            )
            modified_code.extend([indent + line for line in function_body[:-1]])
            modified_code.append(f"{indent}}}\n")
            modified_code.append(function_body[-1])
        else:
            modified_code.append(line)
            i += 1
    return "\n".join(modified_code)

def replace_assert_with_require(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    content = content.replace('assert', 'require')
    with open(file_path, 'w') as file:
        file.write(content)

correctness_test, refine_test = core.build_processor_api(
    source_relpath="main_test.go",
    wrap_fn=wrap_go,
    compile_fn=None,
    run_cmd="go test",
    memory_cmd="go test",
    post_write_fn=replace_assert_with_require,
)
