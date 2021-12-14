"""
SUMMARY

Implements regression functions.
"""


import numpy as np

from .sentence_evaluation import logical_evaluator
from .variable.common import Fixed



# Runs Weighted Least Squares with uncorrelated features
# Designed as a first iteration before obtaining the correlated error
# return [coefficient (float), ...]
def wls_uncorrelated(present_tree, available_parent_nodes):

    # Gathers the coefficient variable names
    coef_names = [a_child.value for a_child in present_tree.children[0].children]
    num_coef = len(coef_names)

    datapoint_expressions = [a_child.children for a_child in present_tree.children[1:]]
    num_datapoints = len(datapoint_expressions)
    num_expressions_X = len(datapoint_expressions[0]) - 1

    # Ensures that the length of all the datapoint inputs minus one (because the output y is included)
    #   equals the number of coefficients
    for an_expression in datapoint_expressions:
        assert (len(an_expression) - 1) == num_coef, "The number of datapoint inputs and coefficiens must be the same"

    # Possible trace-input combinations
    num_input_combinations = len(available_parent_nodes)*num_datapoints

    # WLS matrices (without considering the repeated errors)
    X = np.zeros((num_input_combinations, num_coef))
    W = np.zeros((num_input_combinations, num_input_combinations))
    y = np.zeros((num_input_combinations, 1))

    num_parent_nodes = len(available_parent_nodes)

    # Stores the parent node environments
    parent_envs = [a_parent_node.obtain_chain_environment_vars_only() for a_parent_node in available_parent_nodes]
    # Stores the parent node probabilities
    parent_Pr = [a_parent_node.obtain_chain_probability() for a_parent_node in available_parent_nodes]

    # Row index for WLS matrices
    row_index = -1

    # Stores the error values to avoid repeated rows in the error matrix (which would not allow to solve the Least Squares problem)
    # {"error variable (str)":[count(int), row (int)], ...}
    stored_repeated_errors = {}

    # Goes parent node by parent node first
    for a_parent_index in range(0, num_parent_nodes):

        a_parent_node = available_parent_nodes[a_parent_index]
        a_parent_env = parent_envs[a_parent_index]

        # Associated cost equals the probability
        # Less probable traces penalize less
        cost = parent_Pr[a_parent_index]

        # Avoids a cost (must be different to zero)
        #cost_inv = 1/max(cost, 2**(-16))
        cost_inv = max(cost, 2**(-16))

        # Creates a cost variable
        cost_var = Fixed("Cost", cost_inv)


        # Goes input vector by input vector
        for a_datapoint_expressions in datapoint_expressions:

            # Obtains the current row index
            row_index += 1

            # Keeps track of the obtained variables
            tmp_wls_vars = []

            # Goes expression by expression
            for an_expression in a_datapoint_expressions:
                tmp_wls_vars.append(logical_evaluator(an_expression, a_parent_env,
                    final_result=False, numeric_final_result=False))

            # Computes an error variable equal to the variances multiplied by a constant (constant is disregarded)

            error_var = tmp_wls_vars[-1]
            # ε = y - sum_k{ψ_k * x_k}
            for a_tmp_var in tmp_wls_vars[0:num_coef]:
                error_var -= a_tmp_var

            # Calculates the error value
            error_var *= cost_var

            error_var_Var = error_var.variance
            # Avoids zero variance
            error_var_Var = max(error_var_Var, 2**(-16))


            # Inserts the X, W contents
            for col_index in range(0, num_expressions_X):
                X[row_index][col_index] = tmp_wls_vars[col_index].expectation
                W[row_index][row_index] = (cost**2)/(error_var_Var)

            # Inserts the y content
            y[row_index][0] = tmp_wls_vars[-1].expectation


    # Calculate the coefficients
    X_T = np.transpose(X)

    # (X^T)WX
    X_T__W__X = np.dot(np.dot(X_T, W), X)
    # (X^T)Wy (1 D array form)
    X__W__y = [a_y[0] for a_y in  np.dot(np.dot(X_T, W), y)]

    β = np.linalg.solve(X_T__W__X, X__W__y)

    found_coef_vars = []

    for a_coef_index in range(0, num_coef):

        β_k = β[a_coef_index]
        a_coef_name = coef_names[a_coef_index]

        # Creates the corresponding coefficient variables
        # Unknown distribution since the inputs variables may not be normally distributed
        # Assumed discrete
        found_coef_vars.append(Fixed(a_coef_name, β_k))

    return found_coef_vars
