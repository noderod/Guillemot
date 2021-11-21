"""
SUMMARY

Evaluates a sentence, logical only, provided the meaning of the tokens.
"""


import re

from .variable.common import Fixed, generate_true_fixed_var, generate_false_fixed_var
from .variable.logical_variables import logical_value



# Evaluates a sentence logicaLly in a recursive way given the variable environment
# tree_to_be_considered (Parse Tree): Parsed tree corresponding to the expression, or None if no observation (assumed true)
# environment_dict ({"token":variable (Common), ....}): Values (objects) corresponding to each token, environment of the variables,
#  not of the Operating System
# final_result (bool): Whether or not this is the final or a recursion result (if yes, return logical_value object)
# numeric_final_result (bool): Returns the expectation (actual value, not a variable object) in the end
#  useful when utilizing a logical expression as input
def logical_evaluator(tree_to_be_considered, environment_dict, final_result=True, numeric_final_result=False):

    if tree_to_be_considered == None:
        return logical_value.TRUE

    operation_name = tree_to_be_considered.data

    # If it is a variable evaluation, simply return its result
    # https://lark-parser.readthedocs.io/en/latest/classes.html#token
    if operation_name == "e":

        variable_name = tree_to_be_considered.children[0].value

        # Obtains the variable value
        if variable_name in environment_dict:
            operation_logical_value = environment_dict[variable_name]

        # Special case when assigned a value such as true or false
        elif variable_name == "true":
            operation_logical_value = generate_true_fixed_var()
        elif variable_name == "false":
            operation_logical_value = generate_false_fixed_var()


        # Assigns strings as fixed variables
        elif re.match("\".*\"", variable_name):
            contents_str = variable_name.replace("\"", "")
            operation_logical_value = Fixed("PLACEHOLDER", contents_str)

        # Assigns numbers (ints or floats)
        elif numeric_string(variable_name):
            operation_logical_value = Fixed("PLACEHOLDER", float(variable_name))

        else:
            # All variables must be assigned, False if one is not available
            operation_logical_value = generate_false_fixed_var()



    # If it is an "and_operation", follow the tree and return the result recursively
    elif operation_name == "and_operation":

        # Gets the elements to be checked 2 levels down ("and" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, True)
        second_evaluated = logical_evaluator(second_tree, environment_dict, True)


        # Only evaluated true if both values are true
        if (first_evaluated == logical_value.TRUE) and (second_evaluated == logical_value.TRUE):
            operation_logical_value = generate_true_fixed_var()
        else:
            operation_logical_value = generate_false_fixed_var()



    # If it is an "or_operation", follow the tree and return the result recursively
    elif operation_name == "or_operation":

        # Gets the elements to be checked 2 levels down ("and" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, True)
        second_evaluated = logical_evaluator(second_tree, environment_dict, True)


        if (first_evaluated == logical_value.TRUE) or (second_evaluated == logical_value.TRUE):
            operation_logical_value = generate_true_fixed_var()
        else:
            operation_logical_value = generate_false_fixed_var()


    # If it is a "not operation", follow the tree and return the result recursively
    elif operation_name == "not_operation":

        # Gets the element to be checked 2 levels down ("not" tree)
        sole_tree = tree_to_be_considered.children[0].children[0]

        # Evaluates the elements with the same environment and requirements as here
        sole_evaluated  = logical_evaluator(sole_tree, environment_dict, True)

        if sole_evaluated == logical_value.TRUE:
            operation_logical_value = generate_false_fixed_var()
        else:
            operation_logical_value = generate_true_fixed_var()


    elif operation_name == "expectation_operation":

        sole_tree = tree_to_be_considered.children[0].children[0]
        operation_logical_value = logical_evaluator(sole_tree, environment_dict, False).get_expectation()


    elif operation_name == "variance_operation":

        sole_tree = tree_to_be_considered.children[0].children[0]
        operation_logical_value = logical_evaluator(sole_tree, environment_dict, False).get_variance()


    elif operation_name == "equal_operation":

        # Gets the element to be checked 2 levels down ("expect" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # TODO
        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, False)
        second_evaluated = logical_evaluator(second_tree, environment_dict, False)

        operation_logical_value = first_evaluated == second_evaluated


    elif operation_name == "less_operation":

        # Gets the element to be checked 2 levels down ("expect" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # TODO
        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, False)
        second_evaluated = logical_evaluator(second_tree, environment_dict, False)

        operation_logical_value = first_evaluated < second_evaluated


    elif operation_name == "lt_operation":

        # Gets the element to be checked 2 levels down ("expect" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # TODO
        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, False)
        second_evaluated = logical_evaluator(second_tree, environment_dict, False)

        operation_logical_value = first_evaluated <= second_evaluated


    elif operation_name == "greater_operation":

        # Gets the element to be checked 2 levels down ("expect" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # TODO
        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, False)
        second_evaluated = logical_evaluator(second_tree, environment_dict, False)

        operation_logical_value = first_evaluated > second_evaluated


    elif operation_name == "gt_operation":

        # Gets the element to be checked 2 levels down ("expect" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # TODO
        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, False)
        second_evaluated = logical_evaluator(second_tree, environment_dict, False)

        operation_logical_value = first_evaluated >= second_evaluated



    # If requesting a value, return the expectation (value, not a variable object)
    if numeric_final_result:
        return operation_logical_value.expectation


    # Returns the result, checking if indeterminate if needed
    if final_result:
        return operation_logical_value.get_logical_value()
    else:
        return operation_logical_value




# Checks if a certain object can be numeric (float), includes integers
def numeric_string(something):
    try:
        float(something)
        return True
    except:
        return False
