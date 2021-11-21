#!/usr/bin/python3
"""
SUMMARY

Takes command line arguments and reads file contents, interacts with middle layer.
"""


import aux_handler.handler
from inference import inference
import parser.parser



# Reads the goal and file name
[inference_method, program_filepath, calculate_time] = aux_handler.handler.program_inputs()

# Parses the entire file
# Reads the entire file as a string
# https://www.tutorialkart.com/python/python-read-file-as-string/
with open(program_filepath, "r") as ff:
    parsed_program = parser.parser.Program_structure(ff.read(), program_filepath)


# Runs a given inference method
inference.infer(parsed_program, inference_method, calculate_time)
