"""
SUMMARY

Implements an inference circuit and associated elements.
"""


from copy import deepcopy

from .aux_inference import add_to_stack, Simple_Stack, select_random_by_weight
from .sentence_evaluation import logical_evaluator
from .variable.common import generate_true_fixed_var
from .variable.discrete import discrete_creator, generate_bernoulli
from .variable.logical_variables import logical_value



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
            elif present_tree.data == "ite_elseif":

                num_branches = len(present_tree.children)//2
                available_branches = [a_branch_number for a_branch_number in range(0, num_branches)]

                # Keeps track of nodes never accounted for
                never_considered_nodes = []

                for a_parent_node in available_parent_nodes:

                    # Goes condition by condition
                    for a_branch in available_branches:
                        condition = present_tree.children[2*a_branch]
                        contents   = present_tree.children[2*a_branch + 1]

                        if a_parent_node.evaluate_if_condition(condition):
                            future_parent_nodes += self.build_subcircuit(a_parent_node, contents)
                            break

                    else:
                        # No condition has ever been met
                        # Add ihe node as is
                        future_parent_nodes.append(a_parent_node)

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

                # Mark the parent nodes as the current observation nodes
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

                # Mark the parent nodes as the current observation nodes
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
                    future_parent_nodes += [Circuit_node_variable(token_name, a_parent_node, generate_true_fixed_var())]

                available_parent_nodes = future_parent_nodes

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

        # Stores the observation tree
        self.observation_tree = observation_tree

        # Stores the compressed information
        self.compressed_node = compressed_node
        self.compressed_environment = compressed_environment

        self.deadend = deadend

        # Updates the parent node, adding the current node as a child, unless the parent is None (ground node)
        if parents != [None]:

            for ma in range(0, len(parents)):
                self.parents[ma].children.append(self)


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

        # EXPERIMENTAL
        # ---------------------------------------
        recursive_environment = deepcopy(environment_so_far)

        # Updates the environment with the current variable
        # If the variable is already in the environment, do not update
        # This corresponds to leaving the last updated variable value
        if (self.token not in environment_so_far) and (self.token != "OBSERVATION") and (not self.compressed_node):
            recursive_environment[self.token] = [self.variable_value, self.current_probability]

        # Compressed nodes, retrieve all values from their environment
        elif self.compressed_node:
            for a_var_token in self.compressed_environment:
                recursive_environment[self.a_var_token] = [self.compressed_environment[a_var_token], self.probability]


        # ---------------------------------------

        # OLD VERSION
        #environment_so_far[self.token] = [self.binary_value, self.current_probability]

        if self.parents == [None]:
            #print(environment_so_far)
            return environment_so_far
        else:
            return self.parents[0].obtain_chain_environment(recursive_environment)
            # OLD
            #return self.parent.obtain_chain_environment(environment_so_far)


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
        environment_2 = self.obtain_chain_environment()

        # {"variable token":variable_value, ...}
        environment_token_vv = {a_token:environment_2[a_token][0] for a_token in environment_2}

        # Verifies if the output (return) statement is met
        meets_output = logical_value.TRUE == logical_evaluator(given_output_tree, environment_token_vv, True, False)

        return [chain_Pr, meets_output]



    # Evaluates whether or not the upward chain meets an if condition
    def evaluate_if_condition(self, given_condition):

        # Obtains the chain probability
        chain_Pr = self.obtain_chain_probability()

        # Obtains the environment, tokens and variable values only
        environment_2 = self.obtain_chain_environment()

        # {"variable token":variable_value, ...}
        environment_token_vv = {a_token:environment_2[a_token][0] for a_token in environment_2}

        logical_evaluation_result = logical_evaluator(given_condition, environment_token_vv, True, False)

        # Verifies if the output (return) statement is met
        # Not strict due to lazy evaluation
        return (logical_value.TRUE == logical_evaluation_result)



# Creates a circuit node for a variable.
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node_variable(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, token, parent, variable_value):

        # Enforces the token being different from "OBSERVATION"
        assert token not in  ["OBSERVATION", "MARG", "MARGVAR", "ELIM", "ELIMVAR", "DEADEND"], "Token cannot be '%s', reserved name" % (token, )

        Circuit_node.__init__(self, token, observation_node=False, parents=[parent], variable_value=variable_value,
            current_probability=variable_value.probability, observation_tree=None, compressed_node=False,  compressed_environment=None,
            deadend=False)



# Creates a circuit node for an observation.
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node_observation(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, parent, given_observation_tree):

        Circuit_node.__init__(self, "OBSERVATION", observation_node=True, parents=[parent], variable_value=generate_true_fixed_var(),
            current_probability=1, observation_tree=given_observation_tree, compressed_node=False,  compressed_environment=None,
            deadend=False)



# Relevant for variable marginalization and elimination nodes
# This node is used for for storage, it gets the probabilities of the nodes above, but it does not select them itself
class Circuit_node_compressed(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    # pre_compression_nodes (arr) (Circuit_node): Refers to the nodes before compression
    def __init__(self, requested_operation, pre_compression_nodes):
        valid_operations = ["OBSERVATION", "MARG", "MARGVAR", "ELIM", "ELIMVAR", "DEADEND"]
        assert requested_operation in  ["OBSERVATION", "MARG", "MARGVAR", "ELIM", "ELIMVAR"],...
        "Operation must be in '%s', currrently is '%s'" % (str(valid_operations), requested_operation)

        # Obtains all the probabilities
        combined_Pr = 0

        for a_parent_node in pre_compression_nodes:
            combined_Pr += a_parent_node.obtain_chain_probability()

        # Assumed that the variables after compression which have been compressed will not be used
        # and that different compressed nodes will have separate variables of interest
        post_compression_env = pre_compression_nodes[0].obtain_chain_environment()

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