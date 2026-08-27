import os 
import sys
import re
import json

def list_py_files_in_folders(base_path, end_suffix=".py"):
    folder_py_files = {}

    # 获取路径下的所有文件夹
    for root, dirs, files in os.walk(base_path):
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

# this function is to parse the line_profiler report
def parse_profile_output(text):
    lines = text.split('\n')

    # Initialize variables
    total_time = None
    data = []

    # Find 'Total time:'
    for line in lines:
        if 'Total time:' in line:
            # Extract total time
            total_time_str = line.split('Total time:')[1].strip()
            total_time = total_time_str.split()[0]
            break

    # Now find the header line
    header_line_idx = None
    for idx, line in enumerate(lines):
        if line.startswith('Line #'):
            header_line_idx = idx
            break

    if header_line_idx is None:
        print('Header line not found.')
        return

    header_line = lines[header_line_idx]

    # Now get the positions of each column
    columns = ['Line #', 'Hits', 'Time', 'Per Hit', '% Time', 'Line Contents']
    col_positions = []
    for col in columns:
        pos = header_line.find(col)
        col_positions.append(pos)

    # Add end position
    col_positions.append(len(header_line))

    # Now, for each line after the header line + the line of '=' signs
    for line in lines[header_line_idx+2:]:
        # If line is empty, continue
        if not line.strip():
            continue

        # Extract columns based on positions
        values = []
        for i in range(len(col_positions)-1):
            start = col_positions[i]
            end = col_positions[i+1]
            value = line[start:end].strip()
            values.append(value)

        # Now, values is a list of columns
        # Line #, Hits, Time, Per Hit, % Time, Line Contents

        # Check if 'Hits' column is empty
        if values[1] == '':
            # Line only has Line # and Line Contents
            # Shift the Line Contents to the correct position
            line_contents = line[col_positions[0]:].strip()
            values = [values[0], '', '', '', '', line_contents]
        else:
            # All columns are present
            pass

        # Append the parsed values to data
        data.append({
            'Line #': values[0],
            'Hits': values[1],
            'Time': values[2],
            'Per Hit': values[3],
            '% Time': values[4],
            'Line Contents': values[5]
        })

    # Now, total_time and data are extracted
    return total_time, data

#################customized part########################
dat_folder_path = "/storage/ukp/work/zhu1/work/EffiLearner/results/dat_time_profile_exp_ds0"
########################################################


folder_to_file_list = list_py_files_in_folders(dat_folder_path, ".dat")

for folder_path, file_list in folder_to_file_list.items():

    save_info_file = folder_path + "/info.json"
    save_info_json = {}
    
    fastest_total_time = [10000,""]
    slowest_total_time = [0,""]
    
    for file_name in file_list:
        file_name_with_path = folder_path +"/"+file_name
        with open(file_name_with_path,"r") as fp:
            file_data = "".join(fp.readlines())
            try:
                total_time, data = parse_profile_output(file_data)
                total_time = float(total_time)
                save_info_json[file_name] = {"total time":total_time, "detail_analysis":data}
                
                if total_time > 0 and total_time <fastest_total_time[0]:
                    fastest_total_time[0] = total_time
                    fastest_total_time[1] = file_name_with_path

                if total_time >0 and total_time > slowest_total_time[0]:
                    slowest_total_time[0] = total_time
                    slowest_total_time[1] = file_name_with_path
                    
            except Exception as err:
                print("error = {} in file={}".format(err,file_name_with_path))
                continue
                
    save_info_json["fastest_total_time"] = fastest_total_time
    save_info_json["slowest_total_time"] = slowest_total_time
    
    with open(save_info_file, "w") as fw:
        json.dump(save_info_json, fw, indent=4)
    print("finish analysis in folder {}".format(folder_path))