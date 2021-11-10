"""
SUMMARY

Discrete variable, designed to be used as the result of an operation.
"""


from .common import Common



# Generates an array of discrete variables (qualitative or numeric)
# Not a variable itself
class Discrete_Creator(object):

    # "requested_discrete_type": must be "qualitative" or "numeric"
    # "given_variable_name"
    # given_expectations = [...]
    # given_odds = [(float), ...], may be probabilities but not necessarily (no requirement to add up to one, enforced for the total after normalization)
    def __init__(self, requested_discrete_type, given_variable_name, given_expectations, given_odds):

        assert requested_discrete_type in ["qualitative",
                                            "numeric"], "discrete type must be 'qualitative' or 'numeric', it cannot be '%s'" % (requested_discrete_type, )

        combined_odds = sum(given_odds)

        # Creates a set of variables
        self.created_variables = []

        for nv in range(0, len(given_expectations)):
            assigned_probability = given_odds[nv]/combined_odds

            if requested_discrete_type == "qualitative":
                self.created_variables.append(Discrete_Qualitative(given_variable_name, given_expectations[nv], assigned_probability))
            elif requested_discrete_type == "numeric":
                self.created_variables.append(Discrete_Numeric(given_variable_name, given_expectations[nv], assigned_probability))


    # Obtains the created variables
    def get_created_variables(self):
        return self.created_variables



# Discrete qualitative (non-numeric)
class Discrete_Qualitative(Common):

    def __init__(self, given_variable_name, given_expectation, given_probability):

        given_expectation_type = type(given_expectation).__name__

        # Enforces the expectaton to be a string
        assert given_expectation_type == "str", "Discrete qualitative variables must be of type 'str', current type = '%s'" % (given_expectation_type, )

        Common.__init__(self, given_variable_name, "discrete qualitative", given_expectation, 0, given_expectation, given_expectation, given_probability)


    # Different string formatting
    def __str__(self):
        return "Variable(name=\"%s\", class=\"%s\", E = %s, Var=%.4f, range = [%s, %s], Pr = %.4f)" % (self.variable_name, self.variable_class,
                                                                                                self.expectation, self.variance,
                                                                                                self.lower_bound, self.upper_bound,
                                                                                                self.probability)



# Discrete numeric
class Discrete_Numeric(Common):

    def __init__(self, given_variable_name, given_expectation, given_probability):

        given_expectation_type = type(given_expectation).__name__

        # Enforces the expectaton to not be a string
        assert given_expectation_type != "str", "Discrete qualitative variables must not be of type 'str'"

        Common.__init__(self, given_variable_name, "numeric qualitative", given_expectation, 0, given_expectation, given_expectation, given_probability)
