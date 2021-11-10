"""
SUMMARY

Common functions, added here to avoid cluttering.
"""


import os
import sys



# Obtains the command line inputs, verifies that the inference method is either "enumerate" or "rejection"
# Throws exception if not possible
# returns ["inference method", "file name"]
def program_inputs():

    cli_inputs = sys.argv

    # Verifies a correct number of arguments
    if len(cli_inputs) not in  [3, 4]:
        print("Incorrect number of inputs, expected 2 or 3 inputs, %d inputs were provided" % (len(cli_inputs) - 1, ))
        # Exception name obtained from https://docs.python.org/3/tutorial/errors.html
        raise ValueError()

    # Inputs structure
    if len(cli_inputs) == 3:
        inference_method, program_filepath = cli_inputs[1:]

        # Verifies the inference method
        if inference_method not in ["enumerate", "rejection"]:
            print("Inference method must be 'enumerate' or 'rejection', '%s' input was provided" % (inference_method, ))
            raise ValueError()

        # Verifies the file exists
        if not os.path.isfile(program_filepath):
            print("Input filepath does not exist or is not a file")
            raise ValueError()

        calculate_time = False

    elif len(cli_inputs) == 4:
        inference_method, program_filepath, time_command = cli_inputs[1:]

        # Verifies the inference method
        if inference_method not in ["enumerate", "rejection"]:
            print("Inference method must be 'enumerate' or 'rejection', '%s' input was provided" % (inference_method, ))
            raise ValueError()

        # Verifies the file exists
        if not os.path.isfile(program_filepath):
            print("Input filepath does not exist or is not a file")
            raise ValueError()

        if time_command not in ["-T", "--time"]:
            print("Time command not recognized, must be '-T' or '--time', '%s' input was provided" % (time_command, ))
            raise ValueError()

        calculate_time = True

    return [inference_method, program_filepath, calculate_time]
