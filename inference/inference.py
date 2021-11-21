"""
SUMMARY

Implements the inference by search algorithm.
"""


import time

from .inference_circuit import Circuit



# Main function
def infer(given_program_structure, given_inference_method, requested_to_calculate_time):

    # Keeps track of the observed and return values obtained so far
    output_true_so_far = 0
    observed_true_so_far = 0

    instructions_tree = given_program_structure.instructions_tree
    output_tree = given_program_structure.output_tree

    # Generates a circuit from the instructions and evaluated according to the output (return) tree statement
    to_be_inferred = Circuit(instructions_tree, output_tree)

    # Gets times without considering the circuit building time
    t1 = time.time()

    if given_inference_method == "enumerate":
        to_be_inferred.infer_by_enumeration()
    elif given_inference_method == "rejection":
        to_be_inferred.infer_by_rejection()

    t2 = time.time()

    if requested_to_calculate_time:
        print(int(1000*(t2 - t1)))
