"""
SUMMARY

Continuous variables.
"""


from .common import Common




# Common continuous function
# Designed as an abstract class to automatically describe the variable in an unified format
def common_continuous(Common):


    def __init__(self, given_variable_name, given_variable_class, distribution_name, distribution_parameter_names, distribution_parameter_values,
        given_expectation, given_variance, lower_bound, upper_bound, probability):

        # Enforces the same number of parameters names and values
        assert len(distribution_parameter_names) == len(distribution_parameter_names), "Different number of parameter names and values"

        # Joins the parameter names and values with an "=" values
        # Greek alphabet obtained from https://en.wikipedia.org/wiki/Greek_alphabet
        # e.g.: μ=10.000
        parameters_together = []

        for a_pn, a_pv in zip(distribution_parameter_names, distribution_parameter_values):
            parameters_together.append("%s=%.3f" % (a_pn, a_pv))


        formatted_variable_class = distribution_name + "(" + ", ".join(parameters_together) + ")"

        Common.__init__(self, given_variable_name, formatted_variable_class, given_expectation, given_variance, lower_bound, upper_bound, probability)

