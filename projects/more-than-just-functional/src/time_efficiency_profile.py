
# first Step
    # list all decorated py file
    # run the command 
    # save the results into datafile, with suffix as .dat

# second step
    # gather all .dat files and calculate the statistics

import subprocess
import os
from util import *


py_file_folder_path = "profile_py_data/time_opencoder-8b_defaultds_py_data"
save_dat_file_folder_path = "profile_dat_data/time/time_opencoder-8b_defaultds_py_data_1"
runtime_timeout = 20

folder_to_files_dict = list_py_files_in_folders(py_file_folder_path)

for folder_path, py_file_list in folder_to_files_dict.items():

    save_dat_folder_path = save_dat_file_folder_path +"/"+ folder_path.split("/")[-1]
    
    ensure_path_and_file_exists(save_dat_folder_path)
    
    print("py_file_list = {}".format(py_file_list))

    for py_file_name in py_file_list:
        
        save_dat_file_path = save_dat_folder_path +"/"+"".join(py_file_name.split(".")[:-1])+".dat"
        #print("enter {}".format(py_file_name))
        script_name = folder_path+"/"+py_file_name
    
        command = ["kernprof", "-l", "-v", script_name]
        
        """try:
            result = subprocess.run(command, timeout=runtime_timeout, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            with open(save_dat_file_path, "w") as fw:
                fw.write("Total Time: {} s".format(runtime_timeout))
                print("finish one file timeout and save in {}".format(save_dat_file_path))
                continue"""
        try:
            # 执行外部命令并捕获输出
            result = subprocess.run(
                command,
                timeout=runtime_timeout,
                capture_output=True,
                text=True
            )
            
            # 如果需要处理成功输出
            if result.returncode == 0:
                print("{} executed successfully:".format(py_file_name))
                #print(result.stdout)
                with open(save_dat_file_path, "w") as fw:
                    fw.write(result.stdout)
            else:
                print("{} failed with return code:{}".format(py_file_name,result.returncode))
                #print("Error message:", result.stderr)

        except subprocess.TimeoutExpired:
            # 超时处理逻辑
            with open(save_dat_file_path, "w") as fw:
                fw.write("Total Time: {} s".format(runtime_timeout))
                print(f"Execution timed out. Result saved in {save_dat_file_path}")
                continue
        except Exception as e:
            # 捕获所有其他异常
            print("An unexpected error occurred:")
            print(e)
            continue
    
        #print("finish one file and save in {}".format(save_dat_file_path))
    print("finish one folder at {}".format(folder_path))