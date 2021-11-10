"""
SUMMARY

Evaluates a sentence, logical only, provided the meaning of the tokens.
"""


from .variable_values import variable_value
from .variable_values import opposite_values



# Rapidly translates "true"/"false" to the corresponding logical value
logical_mapper = {"true":variable_value.TRUE, "false":variable_value.FALSE}



# Evaluates a sentence logicaLly provided token meanings in a recursive way
# tree_to_be_considered (Parse Tree): Parsed tree corresponding to the expression, or None if no observation (assumed true)
# environment_dict ({"token":variable_value, ....}): Values corresponding to each token, environment of the variables, not of the Operating System
# strict (bool): Undetermined is treated as False
# enforce_known_variable (bool): Variables missing result in them being considered False
def logical_evaluator(tree_to_be_considered, environment_dict, strict=False, enforce_known_variable=False):

    if tree_to_be_considered == None:
        return variable_value.TRUE

    operation_name = tree_to_be_considered.data

    # If it is a variable evaluation, simply return its result
    # https://lark-parser.readthedocs.io/en/latest/classes.html#token
    if operation_name == "e":

        variable_name = tree_to_be_considered.children[0].value

        # Obtains the variable value, indeterminate if not within the environment
        if variable_name in environment_dict:
            operation_logical_value = environment_dict[variable_name]

        # Special case when assigned a value such as true or false
        elif variable_name in ["true", "false"]:
            operation_logical_value = logical_mapper[variable_name]

        else:
            # Error if all variables must have an assigned value
            if enforce_known_variable:
                operation_logical_value = variable_value.FALSE

            operation_logical_value = variable_value.INDETERMINATE


    # If it is an "and_operation", follow the tree and return the result recursively
    elif operation_name == "and_operation":

        # Gets the elements to be checked 2 levels down ("and" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, strict, enforce_known_variable)
        second_evaluated = logical_evaluator(second_tree, environment_dict, strict, enforce_known_variable)


        # Only evaluated true if both values are true
        if (first_evaluated == variable_value.TRUE) and (second_evaluated == variable_value.TRUE):
            operation_logical_value = variable_value.TRUE
        elif (first_evaluated == variable_value.FALSE) or (second_evaluated == variable_value.FALSE):
            operation_logical_value = variable_value.FALSE
        else:
            operation_logical_value = variable_value.INDETERMINATE

    # If it is an "or_operation", follow the tree and return the result recursively
    elif operation_name == "or_operation":

        # Gets the elements to be checked 2 levels down ("and" tree)
        first_tree, second_tree = tree_to_be_considered.children[0].children

        # Evaluates the elements with the same environment and requirements as here
        first_evaluated  = logical_evaluator(first_tree, environment_dict, strict, enforce_known_variable)
        second_evaluated = logical_evaluator(second_tree, environment_dict, strict, enforce_known_variable)


        if (first_evaluated == variable_value.FALSE) and (second_evaluated == variable_value.FALSE):
            operation_logical_value = variable_value.FALSE
        elif (first_evaluated == variable_value.TRUE) or (second_evaluated == variable_value.TRUE):
            operation_logical_value = variable_value.TRUE
        else:
            operation_logical_value = variable_value.INDETERMINATE

    # If it is a "not operation", follow the tree and return the result recursively
    elif operation_name == "not_operation":

        # Gets the element to be checked 2 levels down ("not" tree)
        sole_tree = tree_to_be_considered.children[0].children[0]

        # Evaluates the elements with the same environment and requirements as here
        sole_evaluated  = logical_evaluator(sole_tree, environment_dict, strict, enforce_known_variable)

        operation_logical_value = opposite_values[sole_evaluated]


    # Returns the result, checking if indeterminate if needed
    return evaluate_content_indeterminate_as_false(operation_logical_value, strict)



# Evaluates avariable or sentence result as false if indeterminate and strict_evaluation=True, returns its original value if not
def evaluate_content_indeterminate_as_false(given_result, strict_evaluation=False):

    if (given_result == variable_value.INDETERMINATE) and strict_evaluation:
        return variable_value.FALSE

    return given_result

