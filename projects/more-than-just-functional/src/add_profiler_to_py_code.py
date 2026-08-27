import os
import ast
import sys

from util import *


ListNode_text = """
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
"""
TreeNode_text = """
class TreeNode:
    def __init__(self, val=0, left=None, right=None, next=None):
        self.val = val
        self.left = left
        self.right = right
        self.next = next
"""

import_pkg = """
from typing import *
from bisect import *
from collections import *
from copy import *
from datetime import *
from heapq import *
from math import *
from re import *
from string import *
from random import *
from itertools import *
from functools import *
from operator import *

import string
import re
import datetime
import collections
import heapq
import bisect
import copy
import math
import random
import itertools
import functools
import operator
import re
import sys
import linecache
"""

memory_profiler_prompt = r"""
def parse_profile_table(profile_table: str):
    table = {"filename": None, "rows": []}
    for line in profile_table.strip().split("\n"):
        if line.startswith("Filename:"):
            table["filename"] = line.split(": ")[1]
        elif re.match(r"^\s*\d+", line):
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=4)
            if len(parts) == 5 and "iB" in parts[1] and "iB" in parts[2]:
                table["rows"].append({
                    "line": int(parts[0]),
                    "mem_usage": parts[1],
                    "increment": parts[2],
                    "occurrences": int(parts[3]),
                    "line_contents": parts[4],
                })
            else:
                parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
                table["rows"].append({
                    "line": int(parts[0]),
                    "line_contents": parts[1] if len(parts) == 2 else "",
                })
    return table

def print_averaged_results(profile_log: str, precision: int = 1):
    tables = [parse_profile_table(table) for table in profile_log.split("\n\n\n")]
    averaged_table = defaultdict(lambda: defaultdict(list))

    for table in tables:
        filename = table["filename"]
        for row in table["rows"]:
            line = row["line"]
            if "mem_usage" in row:
                mem_usage = float(row["mem_usage"].split()[0])
                increment = float(row["increment"].split()[0])
                occurrences = row["occurrences"]
                averaged_table[filename][line].append((mem_usage, increment, occurrences))
            else:
                averaged_table[filename][line].append(tuple())

    stream = sys.stdout
    template = '{0:>6} {1:>12} {2:>12}  {3:>10}   {4:<}'

    for filename, lines in averaged_table.items():
        header = template.format('Line #', 'Mem usage', 'Increment', 'Occurrences', 'Line Contents')

        stream.write(u'Filename: ' + filename + '\n\n')
        stream.write(header + u'\n')
        stream.write(u'=' * len(header) + '\n')

        all_lines = linecache.getlines(filename)

        float_format = u'{0}.{1}f'.format(precision + 4, precision)
        template_mem = u'{0:' + float_format + '} MiB'

        for lineno, mem_values in lines.items():
            # TODO: should average the rest or not?
            # mem_values = [(50.1, 0.0, 4), (51.1, 0.0, 6), ()]
            if any([len(m) == 0 for m in mem_values]):
                tmp = template.format(lineno, "", "", "", all_lines[lineno - 1])
            else:
                mem_usage_sum = sum(m[0] for m in mem_values)
                increment_sum = sum(m[1] for m in mem_values)
                occurrences_sum = sum(m[2] for m in mem_values)
                count = len(mem_values)

                avg_mem_usage = mem_usage_sum / count
                avg_increment = increment_sum / count
                avg_occurrences = occurrences_sum / count

                avg_mem_usage_str = template_mem.format(avg_mem_usage)
                avg_increment_str = template_mem.format(avg_increment)

                tmp = template.format(lineno, avg_mem_usage_str, avg_increment_str, int(avg_occurrences), all_lines[lineno - 1])
            stream.write(tmp)

print_averaged_results(profile_stream.getvalue(), precision=PROFILE_PRECISION)
"""

memory_profiler_pkgs = r"""
from collections import defaultdict, deque
from memory_profiler import profile
import io
profile_stream = io.StringIO()
PROFILE_PRECISION = 1
"""

### Self-defined parameters
py_file_folder = "py_data/n-best_opencoder-8b_defaultds_py_data"
profiler_file_save_folder = "profile_py_data/time_opencoder-8b_defaultds_py_data"
profile_type = "time" # can be 'memory' or 'time'

foler_to_files_dict = list_py_files_in_folders(py_file_folder)

for folder_path, file_list in foler_to_files_dict.items():
    folder_name = folder_path.strip().split("/")[-1]
    profiler_file_save_path = profiler_file_save_folder+"/"+folder_name
    ensure_path_and_file_exists(profiler_file_save_path)
    
    for py_file_name in file_list:
        py_profiler_file_name = profiler_file_save_path +"/"+ py_file_name.split(".")[0]+f'_{profile_type}.py'
        py_file_path = folder_path+"/"+py_file_name
        
        with open(py_file_path, "r") as fp:
            py_code = "".join(fp.readlines())
            try:
                if profile_type == "memory":
                    py_code_with_profiler, test_cases, entry_point = extract_assert_tests_and_add_profiler(py_code,"memory")
                    full_py_code_with_profiler = memory_profiler_pkgs+"\n\n"+import_pkg+"\n\n"+py_code_with_profiler+"\n\n"+memory_profiler_prompt
                elif profile_type == "time":
                    py_code_with_profiler, test_cases, entry_point = extract_assert_tests_and_add_profiler(py_code,"time")
                    full_py_code_with_profiler = import_pkg+"\n\n"+py_code_with_profiler
                else:
                    print("Error!, profiler type should either 'memory' or 'time' ")
                    
            except Exception as err:
                print("error in {}, info={}".format(py_file_path, err))
                continue
        with open(py_profiler_file_name, "w") as fw:
            fw.write(full_py_code_with_profiler)