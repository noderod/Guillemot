"""
SUMMARY

Auxiliary functions, added here to avoid clutter.
"""


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
