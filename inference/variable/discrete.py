"""
SUMMARY

Discrete variables.
"""


from .common import Common



# Generates an array of discrete variables (qualitative or numeric)
# "requested_discrete_type": must be "qualitative" or "numeric"
# "given_variable_name"
# given_expectations = [...] assigned values to the variables (5, "cat")
# given_odds = [(float), ...], may be probabilities but not necessarily (no requirement to add up to one, enforced for the total after normalization)
def discrete_creator(requested_discrete_type, given_variable_name, given_expectations, given_odds):

    assert requested_discrete_type in ["qualitative",
                                        "numeric"], "discrete type must be 'qualitative' or 'numeric', it cannot be '%s'" % (requested_discrete_type, )

    combined_odds = sum(given_odds)

    # Creates a set of variables
    created_variables = []

    for nv in range(0, len(given_expectations)):
        assigned_probability = given_odds[nv]/combined_odds

        if requested_discrete_type == "qualitative":
            created_variables.append(Discrete_Qualitative(given_variable_name, given_expectations[nv], assigned_probability))
        elif requested_discrete_type == "numeric":
            created_variables.append(Discrete_Numeric(given_variable_name, given_expectations[nv], assigned_probability))


    return created_variables



# Creates a Bernoulli (flip) variable
# 0 <= (p =given_Pr) <= 1
def generate_bernoulli(given_variable_name, given_Pr):
    assert (0 <= given_Pr) and (given_Pr <= 1), "Required 0 <= p <= 1, p =%.4f" % (given_Pr, )
    return discrete_creator("numeric", given_variable_name, [0, 1], [1 - given_Pr, given_Pr])



# Discrete qualitative (non-numeric)
class Discrete_Qualitative(Common):

    def __init__(self, given_variable_name, given_expectation, given_probability):

        given_expectation_type = type(given_expectation).__name__

        # Enforces the expectaton to be a string
        assert given_expectation_type == "str", "Discrete qualitative variables must be of type 'str', current type = '%s'" % (given_expectation_type, )

        Common.__init__(self, given_variable_name, "discrete qualitative", given_expectation, 0, given_expectation, given_expectation, given_probability)



# Discrete numeric
class Discrete_Numeric(Common):

    def __init__(self, given_variable_name, given_expectation, given_probability):

        given_expectation_type = type(given_expectation).__name__

        # Enforces the expectaton to not be a string
        assert given_expectation_type != "str", "Discrete numeric variables must not be of type 'str'"

        Common.__init__(self, given_variable_name, "numeric qualitative", given_expectation, 0, given_expectation, given_expectation, given_probability)
