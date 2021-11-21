"""
SUMMARY

Auxiliary functions, added here to avoid clutter.
"""


from bisect import bisect_left
import random



# Selects a random item by weight
# It is not necessary for the float to be aprobability, although it always is for Guillemot purposes
# All weights must be positive
# Items with zero wight are ignored
# given_selection = [[object, weight (float)], ...]
# return the item itself (not the weight)
def select_random_by_weight(given_selection):

    # There must be at least one item
    assert given_selection != [], "Item selection cannot be empty list"

    # Obtains an array to store the weight positions
    weight_positions = [0]
    possible_items = []

    for a_pair in given_selection:
        an_item, a_weight = a_pair

        assert a_weight >= 0, "All weights must > 0. currently = %.4f" % (a_weight, )

        if a_weight != 0:
            possible_items.append(an_item)
            weight_positions.append(weight_positions[-1] + a_weight)

    # If no items (all have probability equal zero), simply return the first item
    if possible_items == []:
        return given_selection[0][0]

    # Selects a random location within the interval
    some_location_within_interval = random.uniform(weight_positions[0], weight_positions[-1])

    # Finds its location
    # Based on https://www.geeksforgeeks.org/binary-search-bisect-in-python/
    # Substracted 1 because this provides the position to the right of the element
    selected_location = bisect_left(weight_positions, some_location_within_interval) - 1

    return given_selection[selected_location][0]



# Determines the starting line of a tree.
def obtain_starting_line(given_tree):

    if type(given_tree).__name__ == "Token":
        return given_tree.line
    else:
        return min(obtain_starting_line(a_subtree) for a_subtree in given_tree.children)



# Puts items in a stack
def add_to_stack(given_stack, given_arr):

    for an_element in given_arr[::-1]:
        given_stack.put(an_element)



# Stack
class Simple_Stack(object):

    # Starts with an empty array
    def __init__(self):
        self.arr = []


    # Adds item to stack, in front of everything else
    def put(self, an_element):
        self.arr = [an_element] + self.arr


    # Retrieves item from the stack
    def get(self):
        retrieved_value = self.arr[0]

        # Updates the stack
        self.arr = self.arr[1:]

        return retrieved_value


    # Finds if the stack still has items within
    def has_contents(self):
        return len(self.arr) != 0
