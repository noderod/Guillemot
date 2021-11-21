"""
SUMMARY

Common variable to inherit from, not designed to be used directly.
"""


from .logical_variables import logical_value



class Common(object):

    def __init__(self, variable_name, variable_class, expectation, variance, lower_bound, upper_bound, probability):
        self.variable_name = variable_name
        self.variable_class = variable_class
        self.expectation = expectation
        self.variance = variance
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

        # Enforces probabality is between 0 and 1
        # ∈ obtained from https://en.wikipedia.org/wiki/Glossary_of_mathematical_symbols
        assert (0 <= probability) and (probability <= 1), "Pr(True) ∈ [0, 1], assigned Pr(True) = %f" % (probability, )

        self.probability = probability


    # Obtains the expectation, as a fixed variable
    def get_expectation(self):
        return Fixed("E[%s]" % (self.variable_name, ), self.expectation)


    # Obtains the variance, as a fixed variable
    def get_variance(self):
        return Fixed("Var[%s]" % (self.variable_name, ), self.variance)


    # Obtains the corresponding logical value
    # false if expectation equals "" or 0, true otherwise
    def get_logical_value(self):
        if (self.expectation == 0) or (self.expectation == ""):
            return logical_value.FALSE
        else:
            return logical_value.TRUE


    # Overloads operators for easier code writing
    # Based on https://www.programiz.com/python-programming/operator-overloading
    # <
    def __lt__(self, another_variable):
        # Upper bound below other variable lower bound, no overlap
        if (self.upper_bound < another_variable.lower_bound) and (not self.overlaps(another_variable)):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var


    # <=
    def __le__(self, another_variable):
        if ((self.upper_bound < another_variable.lower_bound) and (not self.overlaps(another_variable))) or self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var


    # ==
    def __eq__(self, another_variable):
        if self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var


    # >
    def __gt__(self, another_variable):
        if (self.lower_bound > another_variable.upper_bound) and (not self.overlaps(another_variable)):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var


    # >=
    def __ge__(self, another_variable):
        if ((self.lower_bound > another_variable.upper_bound) and (not self.overlaps(another_variable))) or self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var


    # String representation
    def __str__(self):

        # Depending on whether their expectation is a float or a string, it returns the appropriate string format
        if (type(self.expectation).__name__) == "str":
            return "Variable(name=\"%s\", class=\"%s\", E = %s, Var=%.4f, range = [%s, %s], Pr = %.4f)" % (self.variable_name, self.variable_class,
                                                                                                self.expectation, self.variance,
                                                                                                self.lower_bound, self.upper_bound,
                                                                                                self.probability)
        else:

            return "Variable(name=\"%s\", class=\"%s\", E = %.4f, Var=%.4f, range = [%.4f, %.4f], Pr = %.4f)" % (self.variable_name, self.variable_class,
                                                                                                self.expectation, self.variance,
                                                                                                self.lower_bound, self.upper_bound,
                                                                                                self.probability)



    # Checks if there is an overlap between two variables (including edges)
    def overlaps(self, another_variable):
        return (element_is_within(self.lower_bound, another_variable.lower_bound, another_variable.upper_bound)
                        or element_is_within(self.upper_bound, another_variable.lower_bound, another_variable.upper_bound))



# Fixed variable, designed to be used as the result of an operation.
class Fixed(Common):

    def __init__(self, given_variable_name, given_expectation):
        Common.__init__(self, given_variable_name, "fixed", given_expectation, 0, given_expectation, given_expectation, 1)



# Generates a True variable, represented as a 1
def generate_true_fixed_var():
    return Fixed("TRUE", 1)



# Generates a False variable, represented as a 1
def generate_false_fixed_var():
    return Fixed("FALSE", 0)



# Checks if a value is within a range, including the edges
def element_is_within(given_elem, range_lower_bound, range_upper_bound):
    return (range_lower_bound <= given_elem) and (given_elem <= range_upper_bound)
