"""
SUMMARY

Common variable to inherit from, not designed to be used directly.
"""


import random
from uuid import uuid4
import sys

import math

from .logical_variables import logical_value


# Specific number of inner points, fixed for all variables
num_inner_points = 50



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

        # Each variable has inner points, which are not calaculated unless needed to save memory space
        self.inner_points = None 



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


    # Obteins the inner points, only calculated once if needed to save memory space (and then saved)
    def get_inner_points(self):
        if self.inner_points == None:
            # Calculates the inner points and saves them
             self.inner_points = self.calculate_inner_points()

        return self.inner_points



    # Overloads operators for easier code writing
    # Based on https://www.programiz.com/python-programming/operator-overloading
    # <
    def __lt__(self, another_variable):
        # Upper bound below other variable lower bound, no overlap
        if (self.upper_bound < another_variable.lower_bound) and (not self.overlaps(another_variable)):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var()


    # <=
    def __le__(self, another_variable):
        if ((self.upper_bound < another_variable.lower_bound) and (not self.overlaps(another_variable))) or self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var()


    # ==
    def __eq__(self, another_variable):
        if self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var()


    # !=
    def __ne__(self, another_variable):
        if self.overlaps(another_variable):
            return generate_false_fixed_var()
        else:
            return generate_true_fixed_var()


    # >
    def __gt__(self, another_variable):
        if (self.lower_bound > another_variable.upper_bound) and (not self.overlaps(another_variable)):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var()


    # >=
    def __ge__(self, another_variable):
        if ((self.lower_bound > another_variable.upper_bound) and (not self.overlaps(another_variable))) or self.overlaps(another_variable):
            return generate_true_fixed_var()
        else:
            return generate_false_fixed_var()


    # +
    def __add__(self, another_variable):

        # Z = X + Y
        Z = [x + y for x, y in zip(self.get_inner_points(), another_variable.get_inner_points())]

        # E[Z] = E[X] + E[Y]
        E_Z = self.expectation + another_variable.expectation


        # The variance needs to be calculated, always done with trapezoidal integration
        Var_Z = calculate_variance(Z, E_Z)

        A = Common("ADD", "operation result", E_Z, Var_Z,
            self.lower_bound + another_variable.lower_bound,
            self.upper_bound + another_variable.upper_bound,
            1)
        A.inner_points = Z

        return A


    # -
    def __sub__(self, another_variable):

        # Z = X - Y
        Z = [x - y for x, y in zip(self.get_inner_points(), another_variable.get_inner_points())]

        # E[Z] = E[X] - E[Y]
        E_Z = self.expectation - another_variable.expectation


        # The variance needs to be calculated, always done with trapezoidal integration
        Var_Z = calculate_variance(Z, E_Z)

        A = Common("SUBSTRACT", "operation result", E_Z, Var_Z,
            self.lower_bound - another_variable.upper_bound,
            self.upper_bound + another_variable.lower_bound,
            1)
        A.inner_points = Z

        return A


    # *
    def __mul__(self, another_variable):

        # Z = X * Y
        Z = [x * y for x, y in zip(self.get_inner_points(), another_variable.get_inner_points())]
        E_Z = sum(Z)/len(Z)


        # The variance needs to be calculated, always done with trapezoidal integration
        Var_Z = calculate_variance(Z, E_Z)

        # There are 4 possible combinations of lower and upper points
        a_x, b_x = [self.lower_bound, self.upper_bound]
        a_y, b_y = [another_variable.lower_bound, another_variable.upper_bound]
        pab = [a_x*a_y, a_x*b_y, b_x*a_y, b_x*b_y]


        A = Common("PRODUCT", "operation result", E_Z, Var_Z,
            min(pab),
            max(pab),
            1)
        A.inner_points = Z

        return A


    # /
    def __truediv__(self, another_variable):

        a_x, b_x = [self.lower_bound, self.upper_bound]
        a_y, b_y = [another_variable.lower_bound, another_variable.upper_bound]

        # Z = X / Y
        Z = []
        for x, y in zip(self.get_inner_points(), another_variable.get_inner_points()):

            # If the denominator is zero
            if y == 0:

                # If the numerator is zero, set as 0
                if x == 0:
                    Z.append(0)
                    continue

                # If the denominator bounds are both 0, set as infinity
                # Otherwise skip
                if (a_y == 0) and (b_y == 0):
                    Z.append(calculate_sign(x)*math.inf)

            else:
                Z.append(x/y)



        Z = [x / y for x, y in zip(self.get_inner_points(), another_variable.get_inner_points())]


        E_Z = sum(Z)/len(Z)


        # The variance needs to be calculated, always done with trapezoidal integration
        Var_Z = calculate_variance(Z, E_Z)

        # There are 4 possible combinations of lower and upper points
        pab = [safe_division(a_x, a_y), safe_division(a_x, b_y), safe_division(b_x, a_y), safe_division(b_x, b_y)]

        # If the denominator includes zero within the interval, then the range could be infinite
        if element_is_within(0, a_y, b_y):
            pab.append(math.inf)


        A = Common("DIVISION", "operation result", E_Z, Var_Z,
            min(pab),
            max(pab),
            1)
        A.inner_points = Z

        return A


    # **
    def __pow__(self, another_variable):

        # Z = X ** Y
        Z = [x ** y for x, y in zip(self.get_inner_points(), another_variable.get_inner_points())]
        E_Z = sum(Z)/len(Z)


        # The variance needs to be calculated, always done with trapezoidal integration
        Var_Z = calculate_variance(Z, E_Z)

        # There are 4 possible combinations of lower and upper points
        a_x, b_x = [self.lower_bound, self.upper_bound]
        a_y, b_y = [another_variable.lower_bound, another_variable.upper_bound]
        pab = [safe_exponentiation(a_x, a_y), safe_exponentiation(a_x, b_y), safe_exponentiation(b_x, a_y), safe_exponentiation(b_x, b_y)]


        A = Common("EXPONENTIATION", "operation result", E_Z, Var_Z,
            min(pab),
            max(pab),
            1)
        A.inner_points = Z

        return A



    # Opposite
    # Similar to multiplying the current variable by (-1)
    # Not operator overloading
    def opposite(self):
        A = Common("OPPOSITE", "operation result", -self.expectation, self.variance, -self.upper_bound, -self.lower_bound, 1)

        # Its inner points are those of the original variable multiplied by (-1)
        self.inner_points = [-a for a in self.get_inner_points()]



    # String representation
    def __str__(self):

        # Depending on whether their expectation is a float or a string, it returns the appropriate string format
        if (type(self.expectation).__name__) == "str":
            return "Variable(name=\"%s\", class=\"%s\", E = \"%s\", Var=%.4f, range = [\"%s\", \"%s\"], Pr = %.4f)" % (self.variable_name, self.variable_class,
                                                                                                self.expectation, self.variance,
                                                                                                self.lower_bound, self.upper_bound,
                                                                                                self.probability)
        else:

            return "Variable(name=\"%s\", class=\"%s\", E = %.4f, Var=%.4f, range = [%.4f, %.4f], Pr = %.4f)" % (self.variable_name, self.variable_class,
                                                                                                self.expectation, self.variance,
                                                                                                self.lower_bound, self.upper_bound,
                                                                                                self.probability)

    # Checks if this variable is reached within the boundsa of another
    def is_reached_by_variable_within_bounds(self, another_variable):
        return (element_is_within(self.lower_bound, another_variable.lower_bound, another_variable.upper_bound)
                        or element_is_within(self.upper_bound, another_variable.lower_bound, another_variable.upper_bound))



    # Checks if there is an overlap between two variables (including edges)
    # This requires at least one variable to be within the other's bounds
    def overlaps(self, another_variable):
        return self.is_reached_by_variable_within_bounds(another_variable) or another_variable.is_reached_by_variable_within_bounds(self)



# Fixed variable, designed to be used as the result of an operation.
class Fixed(Common):

    def __init__(self, given_variable_name, given_expectation):
        Common.__init__(self, given_variable_name, "fixed", given_expectation, 0, given_expectation, given_expectation, 1)


    # The inner points are always its value
    def calculate_inner_points(self):
        return [self.expectation for an_inner_point in range(0, num_inner_points)]



# Generates a True variable, represented as a 1
def generate_true_fixed_var():
    return Fixed("TRUE", 1)



# Generates a False variable, represented as a 1
def generate_false_fixed_var():
    return Fixed("FALSE", 0)



# Checks if a value is within a range, including the edges
def element_is_within(given_elem, range_lower_bound, range_upper_bound):
    return (range_lower_bound <= given_elem) and (given_elem <= range_upper_bound)



# Calculates the variance of a given set of points, assuming all of them have the same probability
# Done using the formula from https://en.wikipedia.org/wiki/Variance#Discrete_random_variable
# Note that this does not substract (n-1)
# Z = [(float), ...]
# E_Z (float): Expectation of the values
def calculate_variance(Z, E_Z):

    V = 0

    for a_z in Z:
        V += (a_z - E_Z)**2


    return V/len(Z)



# Calculates a normal division if the denominator is not zero
# If both are zero, return zero
# If the denominator is zero, return infinity
# x/y
def safe_division(x, y):

    if y == 0:

        if x == 0:
            return 0
        else:
            return calculate_sign(x)*math.inf

    else:
        return x/y



# Calculates the exponent, throws exception if the base is negative and the exponent is a float
# x**y
def safe_exponentiation(x, y):

    if (x < 0) and (int(y) != y):
        raise ValueError("Cannot exponentiatiate negative values to a float (requires square root)")
    else:
        return x**y



# Calculates the sign of a number
# 0 has its sign selected randomly
def calculate_sign(x):

    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        # Based on https://docs.python.org/3/library/random.html
        return random.sample([-1, 1])[0]
