"""
SUMMARY

Continuous variables.
"""


from .common import Common

import numpy as np
from scipy.stats import beta
from scipy.stats import norm
from scipy.stats import uniform


integral_resolution = 20 # intervals
integral_points = 1 + integral_resolution



# Common continuous function
# Designed as an abstract class to automatically describe the variable in an unified format
def common_continuous(Common):

    def __init__(self, given_variable_name, distribution_name, distribution_parameter_names, distribution_parameter_values,
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



# Uniform distributions
def uniform_distribution(common_continuous):

    # a (int/float): Start of range
    # b (int/float): End of range
    def __init__(self, given_variable_name, lower_bound, upper_bound, a, b):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.uniform.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=uniform(loc = a, scale = b))

        common_continuous.__init__(self, given_variable_name, "Uniform", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Normal (Gaussian) distributions
def normal_distribution(common_continuous):

    # μ (int/float): Expectationn
    # σ (int/float): Standard deviation
    def __init__(self, given_variable_name, lower_bound, upper_bound, μ, σ):

        # Standardizes variables
        zl = z_standardizer(lower_bound, μ, σ)
        zu = z_standardizer(upper_bound, μ, σ)

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(zl, zu), cdist=norm())

        common_continuous.__init__(self, given_variable_name, "Normal", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Beta distributions
def beta_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, α, β):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=beta(α, β))

        common_continuous.__init__(self, given_variable_name, "Beta", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



# Pareto distributions
def pareto_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, x_m. α):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pareto.html
        # https://en.wikipedia.org/wiki/Pareto_distribution
        # https://towardsdatascience.com/generating-pareto-distribution-in-python-2c2f77f70dbf
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=pareto(α, scale=x_m))

        common_continuous.__init__(self, given_variable_name, "Beta", distribution_parameter_names, distribution_parameter_values,
            E, Var, lower_bound, upper_bound, probability)



pareto(alpha, scale=x_m)

# calculates the z standardization
# z = (x - μ)/σ
def z_standardizer(x, μ, σ):
    return (x - μ)/σ



# Gets a set of equally spaced integral points
# Designed for calculating expectations and variances
def get_integral_points(l, u):
    return np.linspace(l, u, integral_points)



# Gets the points inbetween points of an array
def get_inbetween(given_array):
    A = []

    for nv in range(0, (len(given_array) - 1)):
        A.append(0.5*(given_array[nv] + given_array[nv + 1]))

    return A



# Calculates the probability, expectation, and variance
# ab (arr) (int/float): a, b points
# cdist (scipy.stats.X): Must only take a single value for its "pdf" and "cfd" methods
def get_PR_E_Var(ab, cdist):

    probability = cdist.cdf(ab[-1]) - cdist.cdf(ab[0])

    ab_2 = get_inbetween(ab)

    # Calculates the expectation and variance within the interval
    E   = 0
    Var = 0

    # "integral_resolution" variable could be used instead, but implemented as below for clarity
    for ma in range(0, (integral_points - 1)):
        a = ab[ma]
        b = ab[ma + 1]
        ab_2 = 0.5*(a + b)

        E_f_a = a*cdist.pdf(a)
        E_f_b = b*cdist.pdf(b)
        E_f_ab_2 = ab_2*cdist.pdf(ab_2)

        V_f_a = (a**2)*cdist.pdf(a)
        V_f_b = (b**2)*cdist.pdf(b)
        V_f_ab_2 = (ab_2**2)*cdist.pdf(ab_2)


        # Integral always determined with Simpson's rule (1/3)
        E   += ((b - a)/6)*(E_f_a + 4*E_f_ab_2 + E_f_b)
        Var += ((b - a)/6)*(V_f_a + 4*V_f_ab_2 + V_f_b) - E**2


    # Divides the result by the probability to make it accurate
    E   /= probability
    Var /= probability

    return [probability, E, Var]
