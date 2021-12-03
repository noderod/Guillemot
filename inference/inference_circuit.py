"""
SUMMARY

Implements an inference circuit and associated elements.
"""


from copy import deepcopy
import random
from uuid import uuid4

import matplotlib.pyplot as plt
import numpy as np

from .aux_inference import add_to_stack, Simple_Stack, select_random_by_weight
from .sentence_evaluation import logical_evaluator
from .variable.common import generate_true_fixed_var
from .variable.discrete import discrete_creator, generate_bernoulli
from .variable.continuous import generate_discretized_continuous_distribution, generate_discretized_continuous_distribution_from_n
from .variable.logical_variables import logical_value



# Rapidly matches discrete and continuous parse to the variable type considered by the variable object generator
parsdisc_to_disc = {
    "disc_num":"numeric",
    "disc_qual":"qualitative"
}

parscon_to_con = {
    "d_uniform":"uniform",
    "d_gaussian":"normal",
    "d_pareto":"pareto",
    "d_beta":"beta"
}

parsnumcon_to_con = {
    "d_uniform_num":"uniform",
    "d_gaussian_num":"normal",
    "d_pareto_num":"pareto",
    "d_beta_num":"beta"
}


# Sets a seed for repeatabaility
random.seed(0)



# Creates a Circuit
class Circuit(object):

    # Generates the circuit based on the instruction tree
    def __init__(self, given_instructions_tree, given_output_tree):

        # Creates a ground node at the top
        # Always true
        self.ground_node = Circuit_node_variable(token="GROUND_TOKEN", parent=None, variable_value=generate_true_fixed_var())

        # Keeps track of the final output requirements
        self.output_tree = given_output_tree

        self.bottom_nodes = self.build_subcircuit(self.ground_node, given_instructions_tree)



    # Builds a subcircuit with a given parent node and a tree of items below
    # Implemented as a depth-first search (DFS), always following the left-most child tree if many options are available
    def build_subcircuit(self, given_parent_node, contained_tree):

        # Generates a queue to store child trees to process
        available_trees_to_be_explored = Simple_Stack()

        add_to_stack(available_trees_to_be_explored, contained_tree.children)


        available_parent_nodes = [given_parent_node]

        #available_trees_to_be_explored = contained_tree.children

        # Keep exploring until no more are available
        while available_trees_to_be_explored.has_contents():

            future_trees_to_be_explored = []

            # Gets a tree from the queue
            present_tree = available_trees_to_be_explored.get()

            # Do nothing if not a tree
            if type(present_tree).__name__ != "Tree":
                continue

            future_parent_nodes = []

            data_from_tree = present_tree.data

            # Detect observe nodes
            if data_from_tree == "observe":
                # Gets the observe statement
                observe_statement_tree = present_tree.children[0]

                # Adds the observe statement as a future node
                for a_parent_node in available_parent_nodes:

                    # Only add node if the observation is met

                    # Obtains the environment, tokens and variable values only
                    environment_parent = a_parent_node.obtain_chain_environment()

                    # {"variable token":variable_value, ...}
                    environment_token_parent = {a_token:environment_parent[a_token][0] for a_token in environment_parent}

                    if logical_value.TRUE == logical_evaluator(observe_statement_tree, environment_token_parent, True):
                        future_parent_nodes.append(Circuit_node_observation(a_parent_node, observe_statement_tree))
                    else:
                        # Add deadend nodes to places where the observation is not met
                        # These nodes are not parent nodes
                        Circuit_node_deadend(a_parent_node)


                # Mark the parent nodes as the current observation nodes
                available_parent_nodes = future_parent_nodes



            # Reject statement
            # Opposite of observe, ignore nodes that meet the expression
            elif data_from_tree == "reject":
                # Gets the observe statement
                observe_statement_tree = present_tree.children[0]

                # Adds the observe statement as a future node
                for a_parent_node in available_parent_nodes:

                    # Only add node if the observation is met

                    # Obtains the environment, tokens and variable values only
                    environment_parent = a_parent_node.obtain_chain_environment()

                    # {"variable token":variable_value, ...}
                    environment_token_parent = {a_token:environment_parent[a_token][0] for a_token in environment_parent}

                    if logical_value.FALSE == logical_evaluator(observe_statement_tree, environment_token_parent, True):
                        future_parent_nodes.append(Circuit_node_rejection(a_parent_node, observe_statement_tree))
                    else:
                        # Add deadend nodes to places where the observation is not met
                        # These nodes are not parent nodes
                        Circuit_node_deadend(a_parent_node)


                # Mark the parent nodes as the current observation nodes
                available_parent_nodes = future_parent_nodes


            # Marginalizes one or multiple expressions (note that variables can be expressions too)
            # Nodes which have the same value for all expressions are combined into one when marginalized
            elif data_from_tree == "marg":

                # Obtains the expressions that will be marginalized by
                marginalization_conditions = present_tree.children

                # Stores nodes where the marginalization expressions hold the same values
                # {"[m1, ...]":[Circuit node 1, ...], ...}
                marg_conditions_to_nodes = {}

                # Goes node by node
                for a_parent_node in available_parent_nodes:

                    marginalized_values = []
                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()

                    # Goes condition by condition
                    for a_marg_condition in marginalization_conditions:
                        marginalized_values.append(logical_evaluator(a_marg_condition, environment_parent,
                            final_result=False, numeric_final_result=True))

                    # Checks and stores it in the marginalization conditions as a string
                    marginalized_values_str = str(marginalized_values)
                    if marginalized_values_str in marg_conditions_to_nodes:
                        marg_conditions_to_nodes[marginalized_values_str].append(a_parent_node)
                    else:
                        marg_conditions_to_nodes[marginalized_values_str] = [a_parent_node]


                # Joins the nodes with the same marginalization conditions
                for a_set_of_marg_conditions_values in marg_conditions_to_nodes:
                    nodes_with_same_marginalization_conditions = marg_conditions_to_nodes[a_set_of_marg_conditions_values]


                    future_parent_nodes += [Circuit_node_compressed("MARG", nodes_with_same_marginalization_conditions)]

                # Saves the memory utilized for the marginalization
                del marg_conditions_to_nodes

                available_parent_nodes = future_parent_nodes



            # Eliminates one or multiple variables (only variables themselves may be eliminated, not expressions)
            # It considers the variables utilized in each elimination expression
            # Combines together all nodes which have the same values different values for all the variables not utilized in the expressions
            elif data_from_tree == "elimvar":

                # Obtains the elimination variables in a dictionary for fast access
                elimination_variable_names = {a_child_token.value:True for a_child_token in present_tree.children}

                # Stores nodes where the variables which are not to be eliminated
                # {"[var1, ...]":[Circuit node 1, ...], ...}
                remaining_vars_to_nodes = {}

                # Goes node by node
                for a_parent_node in available_parent_nodes:

                    marginalized_values = []
                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()

                    # Obtains the variables which are not to be eliminated
                    # Sorted for repeatability
                    non_eliminated_vars = sorted([str(environment_parent[a_var]) for a_var in environment_parent if a_var not in elimination_variable_names])

                    # Checks and stores it as a string
                    non_eliminated_vars_str = str(non_eliminated_vars)

                    if non_eliminated_vars_str in remaining_vars_to_nodes:
                        remaining_vars_to_nodes[non_eliminated_vars_str].append(a_parent_node)
                    else:
                        remaining_vars_to_nodes[non_eliminated_vars_str] = [a_parent_node]


                # Joins the nodes with the same marginalization conditions
                for a_set_of_remaining_vars in remaining_vars_to_nodes:
                    nodes_with_same_remaining_vars = remaining_vars_to_nodes[a_set_of_remaining_vars]

                    future_parent_nodes += [Circuit_node_compressed("ELIM", nodes_with_same_remaining_vars, elimination_variable_names)]

                # Saves the memory utilized for the variable elimination
                del remaining_vars_to_nodes

                available_parent_nodes = future_parent_nodes



            # Prints the result of an expression for all parent nodes
            elif data_from_tree == "print":

                node_counter = 0
                expression_to_be_shown = present_tree.children[0]

                for a_parent_node in available_parent_nodes:

                    print("-> Leaf node %d:" % node_counter)

                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()
                    tmp_var = logical_evaluator(expression_to_be_shown, environment_parent, final_result=False, numeric_final_result=False)

                    print("    " + str(tmp_var) + "\n")


                    node_counter += 1



            # Handling if statements, single if statements only
            elif data_from_tree == "ite":

                condition     = present_tree.children[0]
                contents_if   = present_tree.children[1]
                # There is always an else with statements within
                contents_else = present_tree.children[2]

                # Adds the subcircuits to the if conditions
                for a_parent_node in available_parent_nodes:

                    if a_parent_node.evaluate_if_condition(condition):
                        future_parent_nodes += self.build_subcircuit(a_parent_node, contents_if)
                    else:
                        future_parent_nodes += self.build_subcircuit(a_parent_node, contents_else)

                # Update the available to future parent nodes
                available_parent_nodes = future_parent_nodes



            # Handles if statements with optional "else if", but no "else"
            # Only one condition is implemented, if there is a conflict between them, the first one met is implemented
            elif data_from_tree == "ite_elseif":

                num_branches = len(present_tree.children)//2
                available_branches = [a_branch_number for a_branch_number in range(0, num_branches)]

                for a_parent_node in available_parent_nodes:

                    # Goes condition by condition
                    for a_branch in available_branches:
                        condition = present_tree.children[2*a_branch]
                        contents  = present_tree.children[2*a_branch + 1]

                        if a_parent_node.evaluate_if_condition(condition):
                            future_parent_nodes += self.build_subcircuit(a_parent_node, contents)
                            break

                    else:
                        # No condition has ever been met
                        # Add ihe node as is
                        future_parent_nodes.append(a_parent_node)

                # Update the available to future parent nodes
                available_parent_nodes = future_parent_nodes



            # Handles if statements with optional "else if" and required "else"
            # Only one condition is implemented, if a conflict occurs, the first one is implemented
            elif data_from_tree == "ite_complete":

                # Disregard the last branch (else statement)
                num_branches = (len(present_tree.children) -1)//2
                available_branches = [a_branch_number for a_branch_number in range(0, num_branches)]

                for a_parent_node in available_parent_nodes:

                    # Goes condition by condition
                    for a_branch in available_branches:
                        condition = present_tree.children[2*a_branch]
                        contents  = present_tree.children[2*a_branch + 1]

                        if a_parent_node.evaluate_if_condition(condition):
                            future_parent_nodes += self.build_subcircuit(a_parent_node, contents)
                            break

                    else:
                        # No condition has ever been met
                        # Add else conditions
                        contents_else = present_tree.children[-1]
                        future_parent_nodes += self.build_subcircuit(a_parent_node, contents_else)

                # Update the available to future parent nodes
                available_parent_nodes = future_parent_nodes



            # If a node is a flip, add the variable
            elif data_from_tree == "flip":

                # Obtains the token
                token_name = present_tree.children[0].value
                # Values are string, must be transformed back into numbers
                variable_flip_value = float(present_tree.children[1].value)

                # Creates a pair of Bernoulli variables
                b1, b2 = generate_bernoulli(token_name, variable_flip_value)

                # Adds two variable nodes, one for each binary value
                for a_parent_node in available_parent_nodes:

                    future_parent_nodes += [Circuit_node_variable(token_name, a_parent_node, b1),
                                            Circuit_node_variable(token_name, a_parent_node, b2)]

                available_parent_nodes = future_parent_nodes



            # If a node is a bernoulli variable, add the variable (does the same as fip)
            elif data_from_tree == "bern":

                # Obtains the token
                token_name = present_tree.children[0].value

                operation_to_be_executed = present_tree.children[1]

                # Adds two variable nodes, one for each binary value
                for a_parent_node in available_parent_nodes:

                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()
                    assigned_variable_value = logical_evaluator(operation_to_be_executed, environment_parent, final_result=False, numeric_final_result=True)

                    b1, b2 = generate_bernoulli(token_name, assigned_variable_value)

                    future_parent_nodes += [Circuit_node_variable(token_name, a_parent_node, b1),
                                            Circuit_node_variable(token_name, a_parent_node, b2)]

                available_parent_nodes = future_parent_nodes



            # Discrete variables
            elif data_from_tree in parsdisc_to_disc:

                discrete_variable_type = parsdisc_to_disc[data_from_tree]

                variable_name = present_tree.children[0].value

                # Gets the number of discrete value assignments
                num_value_assignments = (len(present_tree.children) - 1)//2

                for a_parent_node in available_parent_nodes:

                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()

                    # Keeps track of the discrete values and their odds
                    assigned_values = []
                    assigned_odds   = []

                    for an_assignment in range(0, num_value_assignments):
                        value_tree = present_tree.children[1 + 2*an_assignment]
                        odds_tree  = present_tree.children[1 + 2*an_assignment + 1]

                        assigned_values.append(logical_evaluator(value_tree, environment_parent, final_result=False, numeric_final_result=True))
                        assigned_odds.append(logical_evaluator(odds_tree, environment_parent, final_result=False, numeric_final_result=True))

                    # Creates the discrete variable
                    generated_variables = discrete_creator(discrete_variable_type, variable_name, assigned_values, assigned_odds)
                    future_parent_nodes += [Circuit_node_variable(variable_name, a_parent_node, a_var) for a_var in generated_variables]


                available_parent_nodes = future_parent_nodes



            # Continuous variables
            elif data_from_tree in parscon_to_con:

                distribution_name = parscon_to_con[data_from_tree]

                variable_name = present_tree.children[0].value

                # Gets the number of discrete value assignments
                num_hyperparameters = len(present_tree.children) - 1

                for a_parent_node in available_parent_nodes:

                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()

                    # Keeps track of the discrete values and their odds
                    assigned_hyperparameters = []

                    for an_hp in range(0, num_hyperparameters):
                        hp_tree = present_tree.children[1 + an_hp]
                        assigned_hyperparameters.append(logical_evaluator(hp_tree, environment_parent, final_result=False, numeric_final_result=True))

                    # Creates the discrete variable
                    generated_variables = generate_discretized_continuous_distribution(variable_name, distribution_name, assigned_hyperparameters)
                    future_parent_nodes += [Circuit_node_variable(variable_name, a_parent_node, a_var) for a_var in generated_variables]


                available_parent_nodes = future_parent_nodes



            # Continuous variables (where intervals are defined as an a number of intervals rather than direct splitting locations)
            elif data_from_tree in parsnumcon_to_con:

                distribution_name = parsnumcon_to_con[data_from_tree]

                variable_name = present_tree.children[0].value

                # Gets the number of discrete value assignments
                num_hyperparameters = len(present_tree.children) - 1

                for a_parent_node in available_parent_nodes:

                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()

                    # Keeps track of the discrete values and their odds
                    assigned_hyperparameters = []

                    for an_hp in range(0, num_hyperparameters):
                        hp_tree = present_tree.children[1 + an_hp]
                        assigned_hyperparameters.append(logical_evaluator(hp_tree, environment_parent, final_result=False, numeric_final_result=True))

                    # Creates the discrete variable
                    generated_variables = generate_discretized_continuous_distribution_from_n(variable_name, distribution_name, assigned_hyperparameters)
                    future_parent_nodes += [Circuit_node_variable(variable_name, a_parent_node, a_var) for a_var in generated_variables]


                available_parent_nodes = future_parent_nodes




            # If a node is an assignment, add this variable
            elif data_from_tree == "assgn":

                token_name = present_tree.children[0].value
                operation_to_be_executed = present_tree.children[1]

                for a_parent_node in available_parent_nodes:

                    # Obtains the environment, tokens and variable values only
                    environment_parent = a_parent_node.obtain_chain_environment_vars_only()
                    assigned_variable = logical_evaluator(operation_to_be_executed, environment_parent, final_result=False, numeric_final_result=False)

                    # Adds node
                    future_parent_nodes += [Circuit_node_variable(token_name, a_parent_node, assigned_variable)]

                available_parent_nodes = future_parent_nodes



            # Shows the circuit
            # No action to the variables themselves is done
            elif data_from_tree == "show_circuit":

                # Gets the ground node
                ground_node = available_parent_nodes[0].obtain_circuit_top()

                # Each node is assigned a number
                # [[Circuit node, assigned number]]
                next_number = 0
                maximum_possible_number = next_number
                origin_node_pairs = [[ground_node, next_number]]

                # Keeps track of seen nodes (relevant for marginalization and maximization nodes)
                # {"Node ID":node number (int), ...}
                seen_nodes = {ground_node.node_ID:next_number}

                # Keeps track of the nodes being joined together per step
                # [[[origin node number, next node number], ...], ...]
                node_conections = []

                while origin_node_pairs != []:

                    # Resets the next pairs of nodes to be explored
                    next_node_pairs = []

                    # Creates a new set of connections at the current step
                    step_connections = []

                    for an_original_node_pair in origin_node_pairs:

                        [original_circuit_node, original_number] = an_original_node_pair

                        # Obtains the node children
                        for a_next_node_pair in original_circuit_node.children:

                            next_circuit_node = a_next_node_pair
                            next_circuit_node_ID = next_circuit_node.node_ID

                            # Obtains the next number
                            if next_circuit_node_ID in seen_nodes:
                                next_number = seen_nodes[next_circuit_node_ID]
                            else:
                                # Assigns a new number
                                maximum_possible_number += 1
                                next_number = maximum_possible_number

                                # Adds the node as seen
                                seen_nodes[next_circuit_node_ID] = next_number

                            # Adds the edge to the graph
                            step_connections.append([original_number, next_number])

                            # Adds the node as a next node to consider
                            next_node_pairs.append([next_circuit_node, next_number])

                    # Replaces the old by the new
                    origin_node_pairs = next_node_pairs

                    # Adds the step connections to be considered
                    node_conections.append(step_connections)


                # Creates a figure to show the nodes
                plt.figure()

                # Finds the maximum width of the circuit
                circuit_max_width = max(len(the_step_connections) for the_step_connections in node_conections)


                # Plots the ground node
                step_counter = 0
                node_height_location = np.linspace(0, circuit_max_width, 3)[1]
                ground_node_xy = [step_counter, node_height_location]

                plt.plot([ground_node_xy[0]], [ground_node_xy[1]], "bo")


                # keeps track of the node locations by node number
                # {node number (int): [x, y]}
                node_locations = {0:ground_node_xy}

                for the_step_connections in node_conections:

                    # Gets the current step number
                    step_counter += 1

                    # Gets the possible height numbers
                    unique_end_nodes_per_level = set([z[1] for z in the_step_connections])

                    possible_height_locations = np.linspace(0, circuit_max_width, 2 + len(unique_end_nodes_per_level))
                    possible_height_locations = possible_height_locations[1:(len(possible_height_locations) -1)]

                    unique_node_counter = -1

                    # Goes through every possible node
                    for nv in range(0, len(the_step_connections)):

                        origin_node_ID, next_node_ID = the_step_connections[nv]

                        # Gets the origin cordinates
                        xo, yo = node_locations[origin_node_ID]

                        # If the node was already known
                        if next_node_ID in node_locations:
                            xn, yn = node_locations[next_node_ID]
                        # Otherwise, calculate these results
                        else:

                            # Get the current node ID
                            unique_node_counter += 1

                            # The x coordinate for the new node is always the step counter
                            xn = step_counter

                            # The y coordinate (height) monotonically increases from the starting point
                            yn = possible_height_locations[unique_node_counter]

                            # Store the results
                            node_locations[next_node_ID] = [xn, yn]


                        # Plots the new node
                        plt.plot([xn], [yn], "bo")

                        # Plots the connection between both
                        plt.plot([xo, xn], [yo, yn], "k-")

                        # Saves the new node coordinates
                        node_locations[next_node_ID] = [xn, yn]


                plt.xlabel("Program step")
                plt.title("Program circuit")

                plt.show()

                # Save memory by deleting no longer useful items
                del seen_nodes, next_node_pairs, origin_node_pairs



            # Otherwise, find the children trees and explore them
            else:
                add_to_stack(available_trees_to_be_explored, present_tree.children)


        # Returns the final parent nodes as the end nodes for the circuit
        return available_parent_nodes



    # Goes down once from the ground node according to the variable probabilities, designed for direct sampling (rejection method)
    # Return [0/1 meeting return statement, 0/1 meeting observations]
    def single_direct_search(self):

        current_node_location = self.ground_node

        while not current_node_location.is_end_node():

            # Finds the children
            available_children = current_node_location.children
            num_children = len(available_children)

            # If there is a single child node, just go there (indicates an observation or a compression node)
            if num_children == 1:
                current_node_location = available_children[0]

            # When there are multiple children, it selects one at random (uniformly)
            else:

                # Selects a child node weighted by its probability
                child_nodes_weighted_by_Pr = [[a_child_node, a_child_node.current_probability] for a_child_node in available_children]
                current_node_location = select_random_by_weight(child_nodes_weighted_by_Pr)


        # In case of deadend, 0 for all
        # Items which do not meet observations cannot meet output requirements
        if current_node_location.deadend:
            return [0, 0]
        else:
            [_Pr_chain, meets_output] = current_node_location.evaluate_chain(self.output_tree)
            return [meets_output, 1]




    # Obtains the rejection (direct search) probability
    # Prints the final results
    def infer_by_rejection(self, num_samples=5000):

        valid_output_observes = 0
        valid_observes = 0


        for a_sample in range(0, num_samples):

            [meets_output, meets_observes] = self.single_direct_search()

            if meets_observes:
                valid_observes += 1

                if meets_output:
                    valid_output_observes += 1

        if (valid_output_observes == 0) and (valid_observes == 0):
            print(0)
            return

        print("%.4f" % (valid_output_observes/valid_observes))




    # Obtains the enumeration (search) probability
    # Goes up from the lowest nodes until the top recording the probabilities
    # Prints the final results
    def infer_by_enumeration(self):

        Pr_meets_output_and_observes = 0
        Pr_meets_observes = 0

        for a_bottom_node in self.bottom_nodes:

            [Pr_chain, meets_output] = a_bottom_node.evaluate_chain(self.output_tree)

            # All the elements at the bottom of the tree meet the observes, otherwise they would not have reached it
            Pr_meets_observes += Pr_chain

            # Not all final tree elements may meet the output requirements
            if meets_output:
                Pr_meets_output_and_observes += Pr_chain

        if (Pr_meets_output_and_observes == 0) and (Pr_meets_observes == 0):
            print(0)
            return

        print("%.4f" % (Pr_meets_output_and_observes/Pr_meets_observes))



    # Shows the circuit
    def show_circuit(self):
        self.ground_node.show_bottom_circuit()






# Creates a circuit node.
# Each node has 1 token, 1 or more parents (None if it is the circuit head), a value (variable object), and probailities of it being true
# probability_true (float): Refers to the probability of the node itself, this is useful for variable marginalization or elimination
# compressed_node (bool): Refers to nodes after marginalization or elimination (where the probabilities and environments are stored directly)
# compressed_environment {"variable token":variable value}: Environment present in compressed nodes
# deadend (bool): Creates a dead-end node, designed to mark nodes which do not meet observations
class Circuit_node(object):

    def __init__(self, token, observation_node, parents, variable_value, current_probability, observation_tree, compressed_node = False,
        compressed_environment = None, deadend = False):

        self.token = token

        # Requires parents to be a list
        assert type(parents) == list, "Provided parents must be a list"

        self.parents = parents

        self.observation_node = observation_node

        # No children nodes as of now
        self.children = []

        self.variable_value = variable_value


        # Enforces probabality is between 0 and 1
        # ∈ obtained from https://en.wikipedia.org/wiki/Glossary_of_mathematical_symbols
        assert (0 <= current_probability) and (current_probability <= 1), "Pr ∈ [0, 1], assigned Pr = %.4f" % (current_probability, )

        self.current_probability = current_probability

        # Stores the observation or rejection tree
        # Rejection trees act the same as a negated obseervation
        self.observation_tree = observation_tree

        # Stores the compressed information
        self.compressed_node = compressed_node
        self.compressed_environment = compressed_environment

        self.deadend = deadend

        # Updates the parent node, adding the current node as a child, unless the parent is None (ground node)
        if parents != [None]:

            for ma in range(0, len(parents)):
                self.parents[ma].children.append(self)

        # Assigns an unique ID to each node
        self.node_ID = str(uuid4())


    # Custom node representation in string form
    # Obtained using "OneCricketeer" and "Ignacio Vazquez-Abrams"'s answer from
    # https://stackoverflow.com/questions/4932438/how-to-create-a-custom-string-representation-for-a-class-object
    def __str__(self):
        return "CIRCUIT NODE(token=\"%s\", variable value=(%s), Pr = %.4f)" % (self.token, self.variable_value, self.current_probability)


    # Shows a node and the ones below in a recursive manner with 2-indent per level
    def show_bottom_circuit(self, current_indentation = 0):

        # Shows itself
        print(current_indentation*" " + str(self))

        # Shows children nodes with updated indentation
        for a_child_node in self.children:
            a_child_node.show_bottom_circuit(current_indentation + 2)



    # Checks if the node is an end node (no children)
    def is_end_node(self):
        return self.children == []


    # Obtains the probability of the current upwards chain of events, going until the head (self.parent == None)
    # Implemented in a tail-recursive way for efficiency
    def obtain_chain_probability(self, probability_so_far=1):

        if self.parents == [None]:
            return probability_so_far*self.current_probability

        # For compressed nodes (corresponding to variable elimination or marginalization), get their probability as well
        elif self.compressed_node:
            return probability_so_far*self.current_probability
        else:
            return self.parents[0].obtain_chain_probability(probability_so_far*self.current_probability)


    # Obtains the environment dictionary of the current upwards chain of events
    # Implemented in a tail-recursive way for efficiency
    # return environment dictionary = {"token":[variable, current_probability (float)]}
    def obtain_chain_environment(self, environment_so_far = {}):

        recursive_environment = deepcopy(environment_so_far)

        # Updates the environment with the current variable
        # If the variable is already in the environment, do not update
        # This corresponds to leaving the last updated variable value
        if (self.token not in environment_so_far):

            if (self.token != "OBSERVATION") and (not self.compressed_node):
                recursive_environment[self.token] = [self.variable_value, self.current_probability]

            # Compressed nodes, retrieve all values from their environment
            elif self.compressed_node:
                for a_var_token in self.compressed_environment:
                    recursive_environment[a_var_token] = self.compressed_environment[a_var_token]


        if self.parents == [None]:
            #print(environment_so_far)
            return environment_so_far
        else:
            return self.parents[0].obtain_chain_environment(recursive_environment)



    # Obtains the variables alone from a chain/trace
    # return # {"variable token":variable_value, ...}
    def obtain_chain_environment_vars_only(self):
        # Obtains the environment, tokens and variable values only
        complete_environment = self.obtain_chain_environment()

        # {"variable token":variable_value, ...}
        return{a_token:complete_environment[a_token][0] for a_token in complete_environment}



    # Evaluates the upward chain probability and whether or not the upward chain meets the return statement tree as well as the observation lists within
    # Return [Pr(chain) (float), True/False meets output (return) statement tree]
    def evaluate_chain(self, given_output_tree):

        # Obtains the chain probability
        chain_Pr = self.obtain_chain_probability()

        # Obtains the environment, tokens and variable values only
        environment_2 = self.obtain_chain_environment_vars_only()

        # Verifies if the output (return) statement is met
        meets_output = logical_value.TRUE == logical_evaluator(given_output_tree, environment_2, True, False)

        return [chain_Pr, meets_output]



    # Evaluates whether or not the upward chain meets an if condition
    def evaluate_if_condition(self, given_condition):

        # Obtains the chain probability
        chain_Pr = self.obtain_chain_probability()

        # Obtains the environment, tokens and variable values only
        environment_2 = self.obtain_chain_environment_vars_only()

        logical_evaluation_result = logical_evaluator(given_condition, environment_2, True, False)

        # Verifies if the output (return) statement is met
        # Not strict due to lazy evaluation
        return (logical_value.TRUE == logical_evaluation_result)



    # Obtains the node at the top of the circuit
    # Greedily advances via the first parent
    # This is only an issue if going through margnizalization nodess
    def obtain_circuit_top(self):

        # No parents necessarily implies being the top node
        if self.parents == [None]:
            return self
        else:
            return self.parents[0].obtain_circuit_top()


# Creates a circuit node for a variable.
# Each node has 1 token, 1 parent (None if it is the circuit head), a variable, and a probability of being true
class Circuit_node_variable(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, token, parent, variable_value):

        # Enforces the token being different from "OBSERVATION"
        assert token not in  ["OBSERVATION", "MARG", "ELIM", "DEADEND"], "Token cannot be '%s', reserved name" % (token, )

        Circuit_node.__init__(self, token, observation_node=False, parents=[parent], variable_value=variable_value,
            current_probability=variable_value.probability, observation_tree=None, compressed_node=False,  compressed_environment=None,
            deadend=False)



# Creates a circuit node for an observation.
class Circuit_node_observation(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, parent, given_observation_tree):

        Circuit_node.__init__(self, "OBSERVATION", observation_node=True, parents=[parent], variable_value=generate_true_fixed_var(),
            current_probability=1, observation_tree=given_observation_tree, compressed_node=False,  compressed_environment=None,
            deadend=False)



# Creates a circuit node for an rejection.
class Circuit_node_rejection(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, parent, given_observation_tree):

        Circuit_node.__init__(self, "REJECTION", observation_node=True, parents=[parent], variable_value=generate_true_fixed_var(),
            current_probability=1, observation_tree=given_observation_tree, compressed_node=False,  compressed_environment=None,
            deadend=False)



# Relevant for variable marginalization and elimination nodes
# This node is used for for storage, it gets the probabilities of the nodes above, but it does not select them itself
class Circuit_node_compressed(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    # pre_compression_nodes (arr) (Circuit_node): Refers to the nodes before compression
    # variable_names_to_ignore {"variable name":True, ...}: Variable names which are not to be stored
    def __init__(self, requested_operation, pre_compression_nodes, variable_names_to_ignore={}):
        valid_operations = ["MARG", "ELIM", "DEADEND"]
        assert requested_operation in  ["MARG", "ELIM"],...
        "Operation must be in '%s', currrently is '%s'" % (str(valid_operations), requested_operation)

        # Obtains all the probabilities
        combined_Pr = 0

        for a_parent_node in pre_compression_nodes:
            combined_Pr += a_parent_node.obtain_chain_probability()

        # Assumed that the variables after compression which have been compressed will not be used
        # and that different compressed nodes will have separate variables of interest
        post_compression_env = pre_compression_nodes[0].obtain_chain_environment()

        for a_var_to_ignore in variable_names_to_ignore:
            post_compression_env.pop(a_var_to_ignore, None)

        Circuit_node.__init__(self, requested_operation, observation_node=False, parents=pre_compression_nodes, variable_value=generate_true_fixed_var(),
            current_probability=combined_Pr, observation_tree=None, compressed_node=True,  compressed_environment=post_compression_env,
            deadend=False)



# Creates a deadend node
# Designed for traces where observations are not met
class Circuit_node_deadend(Circuit_node):
    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    # pre_compression_nodes (arr) (Circuit_node): Refers to the nodes before compression
    def __init__(self, parent):
        Circuit_node.__init__(self, "DEADEND", observation_node=False, parents=[parent], variable_value=generate_true_fixed_var(),
            current_probability=1, observation_tree=None, compressed_node=False,  compressed_environment=None, deadend=True)