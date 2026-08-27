import subprocess
import re
import time


def probabilistic_model_checking(
    prism_file_path, abstract_state, verified_time, truthfulness_prob, fail_threshold
):

    prism_loc = "prism"
    pm_file = prism_file_path

    spec = (
        "'filter(forall, P>="
        + str(fail_threshold)
        + " [ F<="
        + str(verified_time)
        + " truth_probability<"
        + str(truthfulness_prob)
        + "], state="
        + str(abstract_state)
        + ")'"
    )
    prism_command = prism_loc + " " + pm_file + " -pf " + spec
    # print(prism_command)

    # pmc_start = time.time()
    process = subprocess.Popen(
        prism_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # pmc_end = time.time()
    # print("PMC time: " + str(pmc_end - pmc_start))

    command_output = process.stdout.read().decode("utf-8")
    # print(command_output)
    # print(re.findall(r"Result: (.+?) ", command_output))
    # print("false" in command_output)
    if "true" in command_output:
        return True
    else:
        return False
