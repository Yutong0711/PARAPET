import gc
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
import os
import re


def ensure_path_and_file_exists(file_path):
    """
    检查路径是否存在，如果不存在则创建相应的文件夹和文件。
    :param file_path: 目标文件的路径
    """
    # 分离路径的目录部分和文件部分
    directory = os.path.dirname(file_path)
    
    # 如果目录不存在，递归创建目录
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"create：{directory}")
    
    # 如果文件不存在，创建文件
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        print(f"create：{file_path}")
    else:
        print(f"folder exists：{file_path}")
        
def extract_code_blocks_unsualcase(text):
    # 提取代码块（支持```和~~~，包括语言标识）
    code_block_pattern = r'(^|\n)(?P<fence>`{3,}|~{3,})[^\n]*\n(.*?)(?<=\n)(?P=fence)($|\n)'
    code_blocks = re.findall(code_block_pattern, text, re.DOTALL)
    code_blocks = [match[2] for match in code_blocks]

    # 提取内联代码（`code`）
    inline_code = re.findall(r'`([^`]+?)`', text)

    # 提取缩进的代码块（以4个空格或1个制表符开头的行）
    lines = text.split('\n')
    indented_code_blocks = []
    current_block = []
    in_block = False
    for line in lines:
        if re.match(r'^( {4}|\t)', line):
            current_block.append(line)
            in_block = True
        else:
            if in_block:
                indented_code_blocks.append('\n'.join(current_block))
                current_block = []
                in_block = False
    if current_block:
        indented_code_blocks.append('\n'.join(current_block))

    # 从文本中移除代码块和缩进代码块，防止重复匹配导入语句
    def remove_code_blocks(text):
        return re.sub(code_block_pattern, '', text, flags=re.DOTALL)

    def remove_indented_code(text):
        return re.sub(r'(^|\n)( {4}|\t).*(\n|$)', '', text)

    text_without_code = remove_code_blocks(text)
    text_without_code = remove_indented_code(text_without_code)

    # 提取导入语句（包括多行导入）
    import_pattern = r'''
        ^(?:from[ \t]+\S+[ \t]+import[ \t]+.*(?:\n[ \t]+.*)*)
        |
        ^(?:import[ \t]+.*(?:\n[ \t]+.*)*)
    '''
    import_statements = re.findall(import_pattern, text_without_code, re.MULTILINE | re.VERBOSE)

    # 合并所有代码片段
    all_code_snippets = import_statements + code_blocks + inline_code + indented_code_blocks

    # 返回合并后的代码（不使用 strip()）
    return '\n\n'.join(all_code_snippets)

def extract_python_code_blocks(text):
    """
    从文本中提取所有以```python开头并以```结尾的代码块，保持其原始格式。
    
    :param text: 包含Python代码块的文本
    :return: 一个包含所有Python代码块的列表
    """
    # 正则模式匹配以```python开头，```结尾的代码块
    code_block_pattern = r"```python(.*?)```"
    matches = re.findall(code_block_pattern, text, re.DOTALL)  # re.DOTALL让.可以匹配换行符
    
    # 保持代码块的原始格式
    return matches

def postprocess_code(code):
    """
    Extracts import statements, class definitions, and function definitions
    along with their content from a Python code string.

    Args:
        code (str): A string containing Python code.

    Returns:
        str: A string containing the extracted imports, class, and function definitions.
    """
    def parse_block(lines, indent_level=0):
        """
        Parses lines of code to extract class and function blocks based on indentation.

        Args:
            lines (list): List of lines of code.
            indent_level (int): The current indentation level.

        Returns:
            list: Extracted blocks of code.
        """
        extracted = []
        block = []
        for line in lines:
            # Calculate the indentation of the current line
            stripped = line.lstrip()
            if not stripped:  # Skip empty lines
                continue
            current_indent = len(line) - len(stripped)
            
            # If the line is less indented than the block, finalize the block
            if current_indent <= indent_level and block:
                extracted.append("".join(block))
                block = []

            # If it's a new block (class or def), or it's part of an existing block
            if stripped.startswith("class ") or stripped.startswith("def ") or block:
                block.append(line)

        # Add the last block if any
        if block:
            extracted.append("".join(block))
        return extracted

    # Extract import statements (lines starting with "import" or "from ... import")
    import_pattern = re.compile(r"^(import .*|from .+ import .+)$", re.MULTILINE)
    imports = import_pattern.findall(code)
    imports_code = "\n".join(imports)

    # Split the remaining code into lines and process
    lines = code.splitlines(keepends=True)
    extracted_blocks = parse_block(lines)

    # Combine imports and extracted blocks
    final_code = imports_code + "\n\n" + "\n".join(extracted_blocks)
    return final_code.strip()

model_name = "infly/OpenCoder-8B-Instruct"
#model_name = "bigcode/starcoder2-3b"

basic_prompt = """
<p>You are an optimal performance code generator for <strong>Python</strong>. I will provide a specific task description with some test case examples. Your task is to generate code to solve the task—your implementation code needs optimal performance in accuracy, computational complexity, and memory usage.</p> 

<p>Task:</p>
"""
end_prompt = """
<p>Donot generate any test cases<\p>

<p>Generated Python Code in <strong>class Solution</strong></p>
"""

ds_file = "datasets/dataset.json"

with open(ds_file, "r") as f:
    code_ds = json.load(f)

result_path = "results/n_best_results_ds0"
n_best_num = 50
ds_with_generated_code = []

codemodel = AutoModelForCausalLM.from_pretrained(model_name, 
                                                 torch_dtype=torch.bfloat16,
                                                 device_map="auto",
                                                 trust_remote_code=True)
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

codemodel.eval()

for code_id in range(len(code_ds)):

    code_info = code_ds[code_id]
    task_des = basic_prompt+"\n"+code_info["task_name"]+": "+code_info["description"]+" \n"+end_prompt
    problem_idx = str(code_info["problem_idx"])
    code_info["test_case"] = re.sub(r"'''(.*?)'''", r'"""\1"""', code_info["test_case"])
    testcase_idx = "\n\nsolution=Solution()\n"+code_info["test_case"]
    
    model_inputs = tokenizer.apply_chat_template([{"role":"user", "content":task_des}],add_generation_prompt=True, return_tensors="pt")
    
    with torch.no_grad():
        model_outputs = codemodel.generate(model_inputs.cuda(), max_new_tokens=2056, do_sample=True,pad_token_id=tokenizer.pad_token_id,num_return_sequences=n_best_num)
    model_outputs = [x.cpu() for x in model_outputs]
    
    path4task_result = result_path+"/"+problem_idx

    ensure_path_and_file_exists(path4task_result)

    
    code_info["generated_codes"] = []
    
    for n_best_i in range(len(model_outputs)):
        
        with open(f"{path4task_result}/{problem_idx}_{n_best_i}.py", "w") as fw:
            #generated_py_code = tokenizer.decode(model_outputs[n_best_i][len(model_inputs[0]):], skip_special_tokens=True)
            generated_py_code = tokenizer.decode(model_outputs[n_best_i][:], skip_special_tokens=True)

            code_info["generated_codes"].append(generated_py_code)
            
            generated_py_code = "".join(extract_python_code_blocks(generated_py_code[len(model_inputs[0]):]))
            if len(generated_py_code) == 0:
                generated_py_code = extract_code_blocks_unsualcase(code_info["generated_codes"][-1])
            else:
                generated_py_code = postprocess_code(generated_py_code)
            #generated_py_code = tokenizer.decode(model_outputs[n_best_i], skip_special_tokens=True)
            generated_py_code = generated_py_code + testcase_idx 
            fw.write(generated_py_code)
            
    with open(f"{path4task_result}/info.json","w+") as fw:
        json.dump(code_info, fw, indent=4)
    
    del model_inputs
    del model_outputs
    gc.collect()
    torch.cuda.empty_cache()
    

print("finish")