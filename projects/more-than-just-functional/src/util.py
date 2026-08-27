import json
import os
import re
import ast
import sys

def list_py_files_in_folders(base_path, end_suffix=".py"):
    folder_py_files = {}
    print("within list_py_files_in_folders, folder={}".format(base_path))

    # 获取路径下的所有文件夹
    for root, dirs, files in os.walk(base_path):
        # proflie_dat_data/x.py|y.py 
        if len(dirs) == 0:
            py_files = []
            folder_path = root
            for file in os.listdir(root):
                if file.endswith(end_suffix):
                    py_files.append(file)
            folder_py_files[folder_path] = py_files
                
        else:
            for folder in dirs:
                
                folder_path = os.path.join(root, folder)
                py_files = []
    
                # 列出文件夹中的所有 .py 文件
                for file in os.listdir(folder_path):
                    if file.endswith(end_suffix):
                        py_files.append(file)
    
                # 将文件夹路径和 .py 文件列表存储到字典中
                folder_py_files[folder_path] = py_files

    return folder_py_files

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
        
class ProfilerTransformer(ast.NodeTransformer):
    def __init__(self, target_function, profile_type="time"):
        self.target_function = target_function
        self.profile_type = profile_type

    def visit_FunctionDef(self, node):
        if node.name == self.target_function:
            # Add the profiler decorator
            if self.profile_type == "time":
                decorator = ast.Name(id='profile', ctx=ast.Load())
            elif self.profile_type == "memory":
                decorator = ast.Call(
                            func=ast.Name(id='profile', ctx=ast.Load()),
                            args=[],
                            keywords=[
                                ast.keyword(arg='stream', value=ast.Name(id='profile_stream', ctx=ast.Load())),
                                ast.keyword(arg='precision', value=ast.Name(id='PROFILE_PRECISION', ctx=ast.Load()))
                            ]
                        )
            else:
                print("error, profile_type need to be 'time' or 'memory'")
                sys.exit()
            node.decorator_list.insert(0, decorator)
        return node

def extract_constant(node):
    """
    提取节点值，支持所有常见类型，包括 UnaryOp（例如 -1）。
    """
    if isinstance(node, ast.Constant):  # 简单常量
        return node.value
    elif isinstance(node, ast.List):  # 列表
        return [extract_constant(el) for el in node.elts]
    elif isinstance(node, ast.Tuple):  # 元组
        return tuple(extract_constant(el) for el in node.elts)
    elif isinstance(node, ast.Dict):  # 字典
        return {extract_constant(key): extract_constant(value) for key, value in zip(node.keys, node.values)}
    elif isinstance(node, ast.Set):  # 集合
        return {extract_constant(el) for el in node.elts}
    elif isinstance(node, ast.UnaryOp):  # 一元操作符
        if isinstance(node.op, ast.UAdd):  # 正号
            return +extract_constant(node.operand)
        elif isinstance(node.op, ast.USub):  # 负号
            return -extract_constant(node.operand)
        elif isinstance(node.op, ast.Not):  # 逻辑非
            return not extract_constant(node.operand)
        else:
            raise ValueError(f"不支持的 UnaryOp 类型: {type(node.op)}")
    else:
        raise ValueError(f"不支持的节点类型: {type(node)}")

def extract_assert_tests_and_add_profiler(code: str, profile_type="time"):
    # Parse the code into an AST
    tree = ast.parse(code)

    # 提取目标函数名称和断言测试用例
    target_function = None
    test_cases = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            # 检查 assert 中是否有目标函数调用
            test = node.test
            if (isinstance(test, ast.Compare) and
                isinstance(test.left, ast.Call) and
                isinstance(test.left.func, ast.Attribute)):
                
                func_name = test.left.func.attr
                if not target_function:
                    target_function = func_name  # 动态提取目标函数名称
                
                # 提取测试用例参数
                args = [extract_constant(arg) for arg in test.left.args]

                # 提取预期结果，支持列表等复杂结构
                expected_value = extract_constant(test.comparators[0])
                test_cases.append({"input": args, "expected": expected_value})

    if not target_function:
        # 检查更详细的情况，如果目标函数仍未识别，则提示错误
        raise ValueError("未找到目标函数调用，请检查 assert 语句的格式是否正确。")
    
    # Transform the AST to add the @profiler decorator
    transformer = ProfilerTransformer(target_function, profile_type)
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    
    # Convert the transformed AST back to source code
    modified_code = ast.unparse(transformed_tree)
    
    return modified_code, test_cases, target_function
