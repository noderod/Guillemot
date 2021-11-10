"""
SUMMARY

Implements an inference circuit and associated elements.
"""


from copy import deepcopy
import random

from .aux_inference import add_to_stack, Simple_Stack
from .sentence_evaluation import logical_evaluator
from .variable_values import variable_value



# Creates a Circuit
class Circuit(object):

    # Generates the circuit based on the instruction tree
    def __init__(self, given_instructions_tree, given_output_tree):

        # Creates a ground node at the top
        # Always true
        self.ground_node = Circuit_node_variable(token="GROUND_TOKEN", parent=None, binary_value=variable_value.TRUE, probability_true=1)

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

            # Detect observe nodes
            if present_tree.data == "observe":
                # Gets the observe statement
                observe_statement_tree = present_tree.children[0]

                #future_parent_nodes = []

                # Adds the observe statement as a future node
                for a_parent_node in available_parent_nodes:

                    # Only add node if the observation is met

                    # Obtains the environment, tokens and variable values only
                    environment_parent = a_parent_node.obtain_chain_environment()

                    # {"variable token":variable_value, ...}
                    environment_token_parent = {a_token:environment_parent[a_token][0] for a_token in environment_parent}

                    if variable_value.TRUE == logical_evaluator(observe_statement_tree, environment_token_parent, strict=True, enforce_known_variable=True):
                        future_parent_nodes.append(Circuit_node_observation(a_parent_node, observe_statement_tree))

                # Mark the parent nodes as the current observation nodes
                available_parent_nodes = future_parent_nodes


            # Handling if statements, single if statements only
            elif present_tree.data == "ite":

                condition     = present_tree.children[0]
                contents_if   = present_tree.children[1]
                # There is always an else with statements within
                contents_else = present_tree.children[2]

                #future_parent_nodes = []

                # Adds the subcircuits to the if conditions
                for a_parent_node in available_parent_nodes:

                    if a_parent_node.evaluate_if_condition(condition):
                        future_parent_nodes += self.build_subcircuit(a_parent_node, contents_if)
                    else:
                        future_parent_nodes += self.build_subcircuit(a_parent_node, contents_else)

                # Update the available to future parent nodes
                available_parent_nodes = future_parent_nodes


            # If a node is a flip, add the variable
            elif present_tree.data == "flip":

                # Obtains the token
                token_name = present_tree.children[0].value
                # Values are string, must be transformed back into numbers
                variable_flip_value = float(present_tree.children[1].value)

                #future_parent_nodes = []

                # Adds two variable nodes, one for each binary value
                for a_parent_node in available_parent_nodes:

                    future_parent_nodes += [Circuit_node_variable(token_name, a_parent_node, variable_value.TRUE,  variable_flip_value),
                                            Circuit_node_variable(token_name, a_parent_node, variable_value.FALSE, variable_flip_value)
                                            ]

                # Mark the parent nodes as the current observation nodes
                available_parent_nodes = future_parent_nodes


            # If a node is an assignment, add this variable
            elif present_tree.data == "assgn":

                # Obtains the token
                token_name = present_tree.children[0].value

                for a_parent_node in available_parent_nodes:

                    # Obtains the environment, tokens and variable values only
                    environment_parent = a_parent_node.obtain_chain_environment()

                    # {"variable token":variable_value, ...}
                    environment_token_parent = {a_token:environment_parent[a_token][0] for a_token in environment_parent}

                    # Calculates the assignment value
                    assigned_value = logical_evaluator(present_tree.children[1], environment_token_parent, strict=True, enforce_known_variable=True)

                    # Adds node
                    future_parent_nodes += [Circuit_node_assigned_variable(token_name, a_parent_node, assigned_value)]

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

            # If there is a single child node, just go there (indicates an if or an observation)
            if num_children == 1:
                current_node_location = available_children[0]
            elif num_children == 2:

                uniform_location = random.random()

                # Finds the true and false children nodes
                cn_1 = current_node_location.children[0]
                cn_2 = current_node_location.children[1]

                if cn_1.binary_value == variable_value.TRUE:
                    t_node = cn_1
                    f_node = cn_2
                else:
                    t_node = cn_2
                    f_node = cn_1

                p_choosing_true_node = t_node.probability_true

                if uniform_location <= p_choosing_true_node:
                    current_node_location = t_node
                else:
                    current_node_location = f_node

            else:
                # There cannot be more than 2 children in a node
                # Note that the zero children case is enforced by the while loop invariable condition
                raise ValueError("Assumption does not hold, more than 2 children in node, num children = %d" % num_children)

        [_Pr_chain, meets_output, meets_observes] = current_node_location.evaluate_chain(self.output_tree)

        return [meets_output, meets_observes]




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

            [Pr_chain, meets_output, meets_observes] = a_bottom_node.evaluate_chain(self.output_tree)

            if meets_observes:
                Pr_meets_observes += Pr_chain

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
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node(object):

    def __init__(self, token, observation_node, parent, binary_value, probability_true, observation_tree):

        self.token = token
        self.parent = parent

        self.observation_node = observation_node

        # No children nodes as of now
        self.children = []

        # Enforces the variable to be either true or false, no indeterminate
        assert (binary_value == variable_value.TRUE) or (binary_value == variable_value.FALSE), ...
        "Binary value must be 'variable_value.TRUE' or 'variable_value.FALSE'"

        self.binary_value = binary_value


        # Enforces probabality is between 0 and 1
        # ∈ obtained from https://en.wikipedia.org/wiki/Glossary_of_mathematical_symbols
        assert (0 <= probability_true) and (probability_true <= 1), "Pr(True) ∈ [0, 1], assigned Pr(True) = %f" % (probability_true, )

        self.probability_true = probability_true

        # Stores the current probability, depends on whether it is true or false
        if self.binary_value == variable_value.TRUE:
            self.current_probability = self.probability_true
        else:
            self.current_probability = 1 - self.probability_true

        # Stores the observation tree
        self.observation_tree = observation_tree

        # Updates the parent node, adding the current node as a child, unless the parent is None (ground node)
        if parent != None:
            self.parent.children.append(self)


    # Custom node representation in string form
    # Obtained using "OneCricketeer" and "Ignacio Vazquez-Abrams"'s answer from
    # https://stackoverflow.com/questions/4932438/how-to-create-a-custom-string-representation-for-a-class-object
    def __str__(self):
        return "CIRCUIT NODE(token=\"%s\", binary value=\"%s\", Pr = %.4f, Pr(T)=%.4f)" % (self.token,
                                                                                            self.binary_value,
                                                                                            self.current_probability,
                                                                                            self.probability_true)



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

        if self.parent == None:
            return probability_so_far*self.current_probability
        else:
            return self.parent.obtain_chain_probability(probability_so_far*self.current_probability)


    # Obtains the environment dictionary of the current upwards chain of events
    # Implemented in a tail-recursive way for efficiency
    # environment dictionary = {"token":[variable_value, current_probability (float)]}
    def obtain_chain_environment(self, environment_so_far = {}):

        # EXPERIMENTAL
        # ---------------------------------------
        recursive_environment = deepcopy(environment_so_far)

        # Updates the environment with the current variable
        # If the variable is already in the environment, do not update
        # This corresponds to leaving the last updated variable value
        if (self.token not in environment_so_far) and (self.token != "OBSERVATION"):
            recursive_environment[self.token] = [self.binary_value, self.current_probability]

        # ---------------------------------------

        # OLD VERSION
        #environment_so_far[self.token] = [self.binary_value, self.current_probability]

        if self.parent == None:
            #print(environment_so_far)
            return environment_so_far
        else:
            return self.parent.obtain_chain_environment(recursive_environment)
            # OLD
            #return self.parent.obtain_chain_environment(environment_so_far)



    # Obtains a list of observation trees up the chain
    # Return [observation tree, ...]
    def obtain_chain_observation_tree(self, observation_list_so_far = []):

        # Add observation tree only if the current node is an observation
        if self.observation_node:
            observation_list_so_far.append(self.observation_tree)

        if self.parent == None:

            # End of the list, there must be at least one observation, so add a None (always evaluated to True as in sentence_evaluator.py) if empty list
            if observation_list_so_far == []:
                return [None]

            return observation_list_so_far
        else:
            return self.parent.obtain_chain_observation_tree(observation_list_so_far)



    # Evaluates the upward chain probability and whether or not the upward chain meets the return statement tree as well as the observation lists within
    # Return [Pr(chain) (float), True/False meets output (return) statement tree, True/False meets observation list trees within]
    def evaluate_chain(self, given_output_tree):

        # Obtains the chain probability
        chain_Pr = self.obtain_chain_probability()

        # Obtains the environment, tokens and variable values only
        environment_2 = self.obtain_chain_environment()

        # {"variable token":variable_value, ...}
        environment_token_vv = {a_token:environment_2[a_token][0] for a_token in environment_2}

        # Obtains the observations in the chain
        necessary_chain_observations = self.obtain_chain_observation_tree()

        # Verifies if the output (return) statement is met
        meets_output = variable_value.TRUE == logical_evaluator(given_output_tree, environment_token_vv, strict=True, enforce_known_variable=True)

        # Verifies that all observations in the chain are met
        meets_observes = all([variable_value.TRUE == logical_evaluator(a_given_observation_tree, environment_token_vv, strict=True,
                                                                        enforce_known_variable=True)
                                for a_given_observation_tree in necessary_chain_observations
                            ])

        return [chain_Pr, meets_output, meets_observes]



    # Evaluates the upward chain probability and whether or not the upward chain meets an if condition
    # Return [Pr(chain) (float), True/False meets output (return) statement tree, True/False meets observation list trees within]
    def evaluate_if_condition(self, given_condition):

        # Obtains the chain probability
        chain_Pr = self.obtain_chain_probability()

        # Obtains the environment, tokens and variable values only
        environment_2 = self.obtain_chain_environment()

        # {"variable token":variable_value, ...}
        environment_token_vv = {a_token:environment_2[a_token][0] for a_token in environment_2}

        # Obtains the observations in the chain
        necessary_chain_observations = self.obtain_chain_observation_tree()

        logical_evaluation_result = logical_evaluator(given_condition, environment_token_vv, strict=False, enforce_known_variable=False)

        # Verifies if the output (return) statement is met
        # Not strict due to lazy evaluation
        return (variable_value.TRUE == logical_evaluation_result)



# Creates a circuit node for a variable.
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node_variable(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, token, parent, binary_value, probability_true):

        # Enforces the token being different from "OBSERVATION"
        assert token != "OBSERVATION", "Token cannot be 'OBSERVATION', reserved name"

        Circuit_node.__init__(self, token, False, parent, binary_value, probability_true, None)



# Creates a circuit node for an observation.
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node_observation(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, parent, given_observation_tree):

        Circuit_node.__init__(self, "OBSERVATION", True, parent, variable_value.TRUE, 1, given_observation_tree)



# Creates a circuit node for a variable assignment, this variable always has a probability of 1 or 0
# Each node has 1 token, 1 parent (None if it is the circuit head), a value (true or false), and probailities of it being true
class Circuit_node_assigned_variable(Circuit_node):

    # Inheritance information obtained from https://www.programiz.com/python-programming/inheritance
    def __init__(self, token, parent, assigned_value):

        # Requires the assigned value to be either true or false
        # Assignments cannot be indeterminate, this would not make sense
        assert (assigned_value == variable_value.TRUE) or (assigned_value == variable_value.FALSE), ...
        "Assigned value must be 'variable_value.TRUE' or 'variable_value.FALSE', it cannot be %s" % (str(assigned_value), )
        # Enforces the token being different from "OBSERVATION"
        assert token != "OBSERVATION", "Token cannot be 'OBSERVATION', reserved name"

        if assigned_value == variable_value.TRUE:
            binary_value = variable_value.TRUE
            probability_true = 1
        elif assigned_value == variable_value.FALSE:
            binary_value = variable_value.FALSE
            probability_true = 0

        Circuit_node.__init__(self, token, False, parent, binary_value, probability_true, None)
