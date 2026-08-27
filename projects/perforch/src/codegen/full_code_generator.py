IMPORT_HELPER = {
    "python": [
        "import math",
        "import re",
        "import sys",
        "import copy",
        "import datetime",
        "import itertools",
        "import collections",
        "import heapq",
        "import statistics",
        "import functools",
        "import hashlib",
        "import numpy",
        "import numpy as np",
        "import string",
        "import pickle",
        "import json",
        "import random",
        "import operator",
        "import bisect",
        "from re import match, search, sub, split, findall, finditer",
        "from sys import maxsize, stdin",
        "from json import loads",
        "from math import floor, ceil, factorial, sqrt, isqrt, inf, log2, log10, sin, cos, tan, pi, e, comb, perm, gcd, lcm",
        "from heapq import heappush, heappop, heapify, heappushpop, nlargest, nsmallest",
        "from bisect import bisect_left, bisect_right",
        "from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits, whitespace, punctuation, hexdigits",
        "from itertools import combinations, permutations, product, groupby, chain, accumulate, zip_longest",
        "from functools import lru_cache, cache, reduce",
        "from collections import OrderedDict, defaultdict, Counter, deque",
        "from typing import Set, Dict, List, Optional, Tuple",
        "from operator import mul",
        "sys.setrecursionlimit(1000000)"
    ],
    "java": [
        "import java.io.*;",
        "import java.math.*;",
        "import java.text.*;",
        "import java.util.*;",
        "import java.util.stream.*;",
        "import java.util.function.*;",
    ],
    "go": [
        "io",
        "os",
        "fmt",
        "math",
        "sort",
        "time",
        "bufio",
        "regexp",
        "reflect",
        "strings",
        "strconv",
        "maps",
        "math/big",
        "math/bits",
        "math/rand",
        "container/heap",
        "container/list",
        "bytes",
        "crypto/md5",
        "testing",
        "github.com/stretchr/testify/require",
    ],
    "cpp": [
        "#include <algorithm>",
        "#include <array>",
        "#include <bitset>",
        "#include <cassert>",
        "#include <chrono>",
        "#include <climits>",
        "#include <cmath>",
        "#include <complex>",
        "#include <condition_variable>",
        "#include <cctype>",
        "#include <cstdio>",
        "#include <cstdlib>",
        "#include <cstring>",
        "#include <deque>",
        "#include <exception>",
        "#include <fstream>",
        "#include <forward_list>",
        "#include <functional>",
        "#include <future>",
        "#include <iomanip>",
        "#include <iostream>",
        "#include <iterator>",
        "#include <list>",
        "#include <map>",
        "#include <memory>",
        "#include <mutex>",
        "#include <numeric>",
        "#include <queue>",
        "#include <random>",
        "#include <set>",
        "#include <sstream>",
        "#include <stack>",
        "#include <stdexcept>",
        "#include <string>",
        "#include <thread>",
        "#include <tuple>",
        "#include <unordered_map>",
        "#include <unordered_set>",
        "#include <utility>",
        "#include <vector>",
        "#include <math.h>",
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <time.h>",
        "using namespace std;",
    ],
    "rust": [
        "use std::mem::{self, replace};",
        "use std::fmt::{self, Display};",
        "use std::iter::{self, FromIterator, repeat, once};",
        "use std::io::{self, Read, Write};",
        "use std::cmp::{self, min, max, Ordering, Reverse};",
        "use std::collections::{self, hash_map::Entry, HashMap, HashSet, BTreeMap, BTreeSet, VecDeque, BinaryHeap};",
        "use std::ops::{self, ControlFlow};",
        "use std::num::{self, NonZeroU32};",
        "struct Solution;"
    ],
}


def generate_full_code(item, language_type, function_definition, benchmark_name):
    try:
        # Extract the code generation based on the language and entry point
        prompt = item["prompt"]
        test = item["test"]
        
        language_type = _normalize_language(language_type)
        benchmark_name = benchmark_name.lower()

        if function_definition == "canonical_solution":
            if benchmark_name == "effibenchx":
                # Effibenchx does not need prompt, the prompt is already in the canonical solution
                prompt = ""
            function_body = item["canonical_solution"]
        else:
            # Generate the function body
            function_body = modify_function_header(function_definition)
            closing = _get_function_closing(benchmark_name, language_type)
            if closing:
                function_body += f"\n{closing}"

        header, foot = _get_header_and_foot(language_type, benchmark_name, prompt, test)


        full_code = "\n".join([
                header,
                function_body,
                foot
            ])

        if benchmark_name == "effibenchx" and language_type == "java":
            # Reason: we need to replace TestSolution with Main to run the code
            full_code = full_code.replace("TestSolution", "Main")
            
        # Use goimports to optimize Go code imports
        if language_type == "go":
            full_code = optimize_go_imports(full_code)
            
        return full_code
    except Exception as e:
        print(f"Error generating full code: {e}")
        return ""

def _normalize_language(language_type: str) -> str:
    language = language_type.lower()
    if language == "python3":
        return "python"
    if language == "golang":
        return "go"
    return language

def _get_function_closing(benchmark_name: str, language_type: str) -> str:
    if benchmark_name == "effibenchx":
        if language_type in {"java", "rust"}:
            return "}"
        if language_type == "cpp":
            return "};"
    elif benchmark_name == "humanevalpack" and language_type == "java":
        return "}"
    return ""

def _get_header_and_foot(language_type: str, benchmark_name: str, prompt: str, test: str):
    if language_type == "python":
        return get_python_header(prompt), test
    if language_type == "cpp":
        return get_cpp_header(prompt), test
    if language_type == "java":
        return get_java_header(prompt), test
    if language_type == "go":
        return get_go_header(prompt), get_go_foot(test)
    if language_type == "rust":
        header = get_rust_header(prompt, benchmark_name)
        foot = test if benchmark_name == "effibenchx" else get_rust_foot(test)
        return header, foot
    return prompt, test

def modify_function_header(function_definition: str):
    '''
    Remove the function header from the given function definition.
    The function header is the first line of the function definition.
    For example, the function header of the following function definition is "def is_happy(s):".
    def is_happy(s):
        return True
    The function definition without the function header is:
        return True
    '''
    code_lines = function_definition.split("\n")
    # remove empty lines
    code_lines = [line for line in code_lines if line.strip()]
    # remove the first line
    code_lines = code_lines[1:]
    return "\n".join(code_lines)

def get_rust_header(prompt: str, benchmark_name: str):
    '''
    Modify the prompt for Rust.
    Reason: we need to add fn main(){} to the test part, but the prompt may already include fn main(){}.
    "fn main(){}" will be removed from the prompt if present.
    '''
    prompt_lines = prompt.split("\n")
    if benchmark_name == "humanevalpack":
        code_lines = [line for line in prompt_lines if line.strip() != "fn main(){}"]
        cleaned_prompt = "\n".join(code_lines)
        header = "\n".join([
            cleaned_prompt
        ])
    elif benchmark_name == "effibenchx":
        additional_import = "\n".join(IMPORT_HELPER["rust"])

        header = "\n".join([
            additional_import,
            prompt
        ])
    return header

def get_rust_foot(test: str):
    '''
    Add fn main(){} to the test part.
    Reason: we add fn main(){} in the test section instead of using #[cfg(test)].
    '''
    
    import re
    test_lines = test.split('\n')
    start_line = None
    end_line = None
    bracket_count = 0
    
    for i, line in enumerate(test_lines):
        # find the first line that starts with "fn test_"
        if re.search(r'^\s*fn\s+test_', line):
            start_line = i + 1
            bracket_count += line.count('{') - line.count('}')
        elif start_line is not None:
            bracket_count += line.count('{') - line.count('}')
            # if the bracket count is 0, we find the end of the function
            if bracket_count == 0:
                end_line = i
                break
    
    if start_line is None or end_line is None:
        raise Exception("No test function found in the test part")
    
    test_function_body_lines = test_lines[start_line:end_line]
    # indent the test function body
    test_function_body = "\n".join([line[4:] if line.startswith('    ') 
                                    else line 
                                    for line in test_function_body_lines])
    # add fn main(){} to the beginning of the test part
    foot = "\n".join([
        "fn main() {",
        test_function_body,
        "}"
    ])
    return foot



def optimize_go_imports(go_code: str) -> str:
    '''
    Use goimports to optimize Go code imports.
    '''
    import subprocess
    import tempfile
    import os
    import shutil
    
    # Locate the goimports executable
    goimports_cmd = None
    
    # 1. First try to find it in PATH
    goimports_cmd = shutil.which('goimports')
    
    # 2. If not found in PATH, use go env to locate it
    if not goimports_cmd:
        try:
            # 获取GOPATH
            result = subprocess.run(['go', 'env', 'GOPATH'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                gopath = result.stdout.strip()
                if gopath:
                    # Linux/Mac
                    goimports_path = os.path.join(gopath, 'bin', 'goimports')
                    if os.path.isfile(goimports_path) and os.access(goimports_path, os.X_OK):
                        goimports_cmd = goimports_path
                    else:
                        # Windows
                        goimports_exe = os.path.join(gopath, 'bin', 'goimports.exe')
                        if os.path.isfile(goimports_exe) and os.access(goimports_exe, os.X_OK):
                            goimports_cmd = goimports_exe
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass
    
    # 3. If still not found, try the default path
    if not goimports_cmd:
        home = os.environ.get('HOME')
        if home:
            default_path = os.path.join(home, 'go', 'bin', 'goimports')
            if os.path.isfile(default_path) and os.access(default_path, os.X_OK):
                goimports_cmd = default_path
    
    # If goimports is not found, return the original code
    if not goimports_cmd:
        print("goimports not found. Please install it with:")
        print("  go install golang.org/x/tools/cmd/goimports@latest")
        print("And make sure $GOPATH/bin is in your PATH, or run:")
        print("  export PATH=$PATH:$(go env GOPATH)/bin")
        return go_code
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as temp_file:
            temp_file.write(go_code)
            temp_file_path = temp_file.name
        
        # Run goimports
        result = subprocess.run(
            [goimports_cmd, '-w', temp_file_path],
            capture_output=True,
            text=True,
            timeout=30  # 30-second timeout
        )
        
        # If goimports succeeds, read the optimized code
        if result.returncode == 0:
            with open(temp_file_path, 'r') as f:
                optimized_code = f.read()
            os.unlink(temp_file_path)
            return optimized_code
        else:
            # If goimports fails, return the original code
            print(f"goimports failed: {result.stderr}")
            os.unlink(temp_file_path)
            return go_code
            
    except subprocess.TimeoutExpired:
        print("goimports timeout")
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        return go_code
    except Exception as e:
        print(f"Error running goimports: {e}")
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        return go_code

def get_go_header(prompt: str):
    # Add all potentially needed imports and let goimports optimize them
    all_imports = []
    for pkg in IMPORT_HELPER["go"]:
        all_imports.append(f'    "{pkg}"')
    
    if all_imports:
        import_section = "import (\n" + "\n".join(all_imports) + "\n)"
    else:
        import_section = ""
    
    header = "\n".join([
        "package main",
        import_section,
        prompt
    ])
    return header

def get_go_foot(test: str):
    '''
    Modify the test part of the given test.
    Reason: if one test case is failed, the whole test will be failed.
    '''
    if test is None:
        test = ""
    foot = test.replace('assert', 'require')
    return foot

def get_cpp_header(prompt: str):
    '''
    Modify the prompt for the given prompt.
    Reason: we need to add the required imports to the prompt
    '''
    additional_import = ""
    for s in IMPORT_HELPER["cpp"]:
        if s not in prompt:
            additional_import += s + "\n"
    header = "\n".join([
        additional_import,
        prompt,
    ])
    return header

def get_python_header(prompt: str):
    '''
    Modify the prompt for the given prompt.
    Reason: we need to add the required imports to the prompt
    '''
    additional_import = "\n".join(IMPORT_HELPER["python"])
    header = "\n".join([
        additional_import,
        prompt
    ])
    return header

def get_java_header(prompt: str):
    '''
    Modify the prompt for the given prompt.
    Reason: we need to add the required imports to the prompt
    '''
    additional_import = "\n".join(IMPORT_HELPER["java"])
    header = "\n".join([
        additional_import,
        prompt
    ])
    return header
