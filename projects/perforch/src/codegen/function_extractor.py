import re

_PY_DEF_RE = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(.*\)\s*(?:->.*)?\s*:")
_C_STYLE_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_CPP_LINE_COMMENT_RE = re.compile(r"//.*$")
_PY_LINE_COMMENT_RE = re.compile(r"#.*$")


class FunctionExtractorError(Exception):
    """Base exception for function extraction failures."""


def _strip_c_style_comments(code: str) -> str:
    return re.sub(_C_STYLE_COMMENT_RE, "", code)


def _strip_cpp_line_comment(line: str) -> str:
    return re.sub(_CPP_LINE_COMMENT_RE, "", line)


def _strip_python_line_comment(line: str) -> str:
    return re.sub(_PY_LINE_COMMENT_RE, "", line)


def _extract_brace_block(lines, start_index):
    bracket_count = 0
    function_lines = []
    for line in lines[start_index:]:
        if "```" in line:
            break
        function_lines.append(line)
        bracket_count += line.count("{") - line.count("}")
        if bracket_count == 0:
            break
    return "\n".join(function_lines)


def _has_brace_in_signature_or_next(lines, start_index):
    line = lines[start_index]
    if "{" in line:
        return True
    for next_line in lines[start_index + 1:]:
        if next_line.strip() == "":
            continue
        return next_line.strip().startswith("{")
    return False


def extract_python_function(file_content, function_name):
    file_content = file_content.replace("\t", "    ")
    lines = file_content.splitlines()
    function_start_line = -1
    in_docstring = False

    for i, raw_line in enumerate(lines):
        line = raw_line
        if "'''" in line or '"""' in line:
            if line.count("'''") + line.count('"""') == 1:
                in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        line = _strip_python_line_comment(line)
        match = _PY_DEF_RE.match(line)
        if match and match.group(1) == function_name:
            function_start_line = i
            break

    if function_start_line == -1:
        raise FunctionExtractorError(
            f"Function '{function_name}' not found in the provided code."
        )

    function_lines = [lines[function_start_line]]
    indent = len(lines[function_start_line]) - len(lines[function_start_line].lstrip())

    for line in lines[function_start_line + 1:]:
        if "```" in line:
            break
        if line.strip() == "" or len(line) - len(line.lstrip()) > indent or line.strip().startswith("# Generation"):
            function_lines.append(line)
        else:
            break

    return "\n".join(function_lines)


# C++ function extraction
def extract_cpp_function(file_content, function_name):
    cleaned = _strip_c_style_comments(file_content)
    lines = cleaned.splitlines()
    function_start_line = -1
    fn_re = re.compile(rf"\b{re.escape(function_name)}\s*\(")

    for i, raw_line in enumerate(lines):
        line = _strip_cpp_line_comment(raw_line)
        if _has_brace_in_signature_or_next(lines, i):
            if fn_re.search(line):
                function_start_line = i
                break

    if function_start_line == -1:
        raise FunctionExtractorError(
            f"Function '{function_name}' not found in the provided code."
        )

    return _extract_brace_block(lines, function_start_line)


# Java function extraction
def extract_java_function(file_content, function_name):
    cleaned = _strip_c_style_comments(file_content)
    lines = cleaned.splitlines()
    function_start_line = -1
    fn_re = re.compile(rf"\b{re.escape(function_name)}\s*\(")

    for i, raw_line in enumerate(lines):
        line = _strip_cpp_line_comment(raw_line)
        if "public " in line and _has_brace_in_signature_or_next(lines, i):
            if fn_re.search(line):
                function_start_line = i
                break

    if function_start_line == -1:
        raise FunctionExtractorError(
            f"Function '{function_name}' not found in the provided code."
        )

    return _extract_brace_block(lines, function_start_line)


# Go function extraction
def extract_go_function(file_content, function_name):
    cleaned = _strip_c_style_comments(file_content)
    lines = cleaned.splitlines()
    function_start_line = -1
    fn_re = re.compile(rf"\b{re.escape(function_name)}\s*\(")

    for i, raw_line in enumerate(lines):
        line = _strip_cpp_line_comment(raw_line)
        if "func " in line and _has_brace_in_signature_or_next(lines, i):
            if fn_re.search(line):
                function_start_line = i
                break

    if function_start_line == -1:
        raise FunctionExtractorError(
            f"Function '{function_name}' not found in the provided code."
        )

    return _extract_brace_block(lines, function_start_line)


# Rust function extraction
def extract_rust_function(file_content, function_name):
    cleaned = _strip_c_style_comments(file_content)
    lines = cleaned.splitlines()
    function_start_line = -1
    fn_re = re.compile(rf"\bfn\s+{re.escape(function_name)}\s*\(")

    for i, raw_line in enumerate(lines):
        line = _strip_cpp_line_comment(raw_line)
        if _has_brace_in_signature_or_next(lines, i):
            if fn_re.search(line):
                function_start_line = i
                break

    if function_start_line == -1:
        raise FunctionExtractorError(
            f"Function '{function_name}' not found in the provided code."
        )

    return _extract_brace_block(lines, function_start_line)


# General extraction function, auto-detects language and calls the respective method
def extract_function_by_language(language: str, code: str, function_name: str):
    '''
    Extract the function from the code by language
    Args:
        language: str, the language of the code
        code: str, the code to extract the function from
        function_name: str, the name of the function to extract
    Returns:
        str, the function
            Example:
                def add(a, b):
                    return a + b
    '''
    language = language.lower()
    extractors = {
        "python": extract_python_function,
        "cpp": extract_cpp_function,
        "go": extract_go_function,
        "java": extract_java_function,
        "rust": extract_rust_function,
    }
    extractor = extractors.get(language)
    if extractor is None:
        raise ValueError(f"Unsupported language: {language}")
    return extractor(code, function_name)
