"""
SUMMARY

Continuous variables.
"""


import random

import numpy as np
from scipy.stats import beta, norm, pareto, uniform

from .common import Common, num_inner_points



integral_resolution = 20 # intervals
integral_points = 1 + integral_resolution



# Creates a number of continuous distributions ranges
# distribution_hp [(float), ...]: Distribution hyperparameters, refers to both distribution parameters (such as the mean) and interval separation points
def generate_discretized_continuous_distribution(given_variable_name, distribution_name, distribution_hp):

    # enforces known distribution
    assert distribution_name in ["uniform", "normal", "beta", "pareto"], "'%s' distribution is not accepted" % (distribution_name, )

    # Enforces all parameters to be numeric
    for a_param in distribution_hp:
        param_type = type(a_param).__name__
        assert (param_type == "int") or (param_type == "float"), "All parameters, must be int or float type, not '%s'" % (param_type, )


    # Generates the different distributions
    if distribution_name == "uniform":

        distribution_parameter_values, ordered_separating_points = obtain_p_sv(distribution_hp, 2)

        a, b = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, a, b)

        # Adds the points to the range as the start and end
        ordered_separating_points = [a] + ordered_separating_points + [b]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(uniform_distribution(given_variable_name, l, u, a, b))

    elif distribution_name == "normal":

        distribution_parameter_values, ordered_separating_points = obtain_p_sv(distribution_hp, 2)

        distribution_parameter_values = distribution_hp[:2]
        separating_points = sorted(distribution_hp[2:])

        μ, σ = distribution_parameter_values

        five_sigma = 5*σ

        # If no interval ranges, utilize 5σ (> 99.9999 of the distribution)
        if ordered_separating_points == []:
            ordered_separating_points = [μ - five_sigma, μ + five_sigma]
        # If there is one or more values, get the ends at 5σ in one distance and 5σ from the peak in the other distance if peak not within values
        else:
            furthest_left  = ordered_separating_points[0]
            furthest_right = ordered_separating_points[-1]

            # Do 5σ in both distances if the peak (μ) is contained within the interval
            if check_within_interval(μ, furthest_left, furthest_right, contains=False):
                ordered_separating_points = [furthest_left - five_sigma] + ordered_separating_points + [furthest_right + five_sigma]

            # Not contained
            # If left of the furthest left, go 5σ left of the peak
            elif μ < (furthest_left - five_sigma):
                ordered_separating_points = [μ - five_sigma] + ordered_separating_points + [furthest_right + five_sigma]
            # if right of the furthest right, go 5σ right of the peak
            else:
                ordered_separating_points = [furthest_left - five_sigma] + ordered_separating_points + [μ + five_sigma]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(normal_distribution(given_variable_name, l, u, μ, σ))


    # Generates the different distributions
    elif distribution_name == "beta":

        distribution_parameter_values, ordered_separating_points = obtain_p_sv(distribution_hp, 2)

        α, β = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, 0, 1)

        # Adds the points to the range as the start and end
        ordered_separating_points = [0] + ordered_separating_points + [1]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(beta_distribution(given_variable_name, l, u, α, β))


    # Generates the different distributions
    elif distribution_name == "pareto":

        distribution_parameter_values, ordered_separating_points = obtain_p_sv(distribution_hp, 2)

        x_m, α = distribution_parameter_values
        enforce_array_within_lu(ordered_separating_points, x_m, np.inf)

        # End point asssigned as the place where CDF >= 0.999999 (close to the 5*σ for the normal distribution)
        if ordered_separating_points == []:
            end_point = x_m/(0.000001**(1/α))
        else:
            end_point = ordered_separating_points[-1] + x_m/(0.000001**(1/α))

        ordered_separating_points = [x_m] + ordered_separating_points + [end_point]

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(pareto_distribution(given_variable_name, l, u, x_m, α))

    return created_distributions



# Creates a number of continuous distributions ranges given a number of splitting locations
# distribution_hp [(float), ...]: Distribution hyperparameters, refers to both distribution parameters (such as the mean) and interval separation points
def generate_discretized_continuous_distribution_from_n(given_variable_name, distribution_name, distribution_hp):

    # enforces known distribution
    assert distribution_name in ["uniform", "normal", "beta", "pareto"], "'%s' distribution is not accepted" % (distribution_name, )

    # Enforces all parameters to be numeric
    for a_param in distribution_hp:
        param_type = type(a_param).__name__
        assert (param_type == "int") or (param_type == "float"), "All parameters, must be int or float type, not '%s'" % (param_type, )


    # Gets the number of blocks (always the last element) as integer
    num_blocks = int(distribution_hp[-1])

    # Enforces it to be larger than zero
    assert num_blocks > 0, "The number of blocks must be rounded to be larger than zero, it currently is %f" % (distribution_hp[-1], )

    # The number of separating points is always 1 larger than the number of blocks
    num_separating_points = 1 + num_blocks

    # Gets the distribution pareameters, which are the remaining hyperparameters
    distribution_parameter_values = distribution_hp[:(len(distribution_hp) - 1)]


    # Generates the different distributions
    if distribution_name == "uniform":

        a, b = distribution_parameter_values

        # Adds the points to the range as the start and end
        ordered_separating_points = np.linspace(a, b, num_separating_points)

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(uniform_distribution(given_variable_name, l, u, a, b))

    elif distribution_name == "normal":

        μ, σ = distribution_parameter_values

        five_sigma = 5*σ

        ordered_separating_points = np.linspace(μ - five_sigma, μ + five_sigma, num_separating_points)

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(normal_distribution(given_variable_name, l, u, μ, σ))


    # Generates the different distributions
    elif distribution_name == "beta":

        α, β = distribution_parameter_values
        # Beta distribution is always within the [0, 1] interval
        ordered_separating_points = np.linspace(0, 1, num_separating_points)

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(beta_distribution(given_variable_name, l, u, α, β))


    # Generates the different distributions
    elif distribution_name == "pareto":

        x_m, α = distribution_parameter_values

        # End point asssigned as the place where CDF >= 0.999999 (close to the 5*σ for the normal distribution)
        end_point = x_m/(0.000001**(1/α))
        ordered_separating_points = np.linspace(x_m, end_point, num_separating_points)

        created_distributions = []

        for wa in range(0, (len(ordered_separating_points) - 1)):
            l = ordered_separating_points[wa]
            u = ordered_separating_points[wa + 1]

            created_distributions.append(pareto_distribution(given_variable_name, l, u, x_m, α))

    return created_distributions




# Common continuous function
# Designed as an abstract class to automatically describe the variable in an unified format
class common_continuous(Common):

    def __init__(self, given_variable_name, distribution_name, distribution_parameter_names, distribution_parameter_values,
        given_expectation, given_variance, lower_bound, upper_bound, probability):

        # Enforces the same number of parameters names and values
        assert len(distribution_parameter_names) == len(distribution_parameter_names), "Different number of parameter names and values"

        # Joins the parameter names and values with an "=" values
        # Greek alphabet obtained from https://en.wikipedia.org/wiki/Greek_alphabet
        # e.g.: μ=10.000
        parameters_together = []

        for a_pn, a_pv in zip(distribution_parameter_names, distribution_parameter_values):
            parameters_together.append("%s=%.4f" % (a_pn, a_pv))


        formatted_variable_class = distribution_name + "(" + ", ".join(parameters_together) + ")"

        Common.__init__(self, given_variable_name, formatted_variable_class, given_expectation, given_variance, lower_bound, upper_bound, probability)



# Uniform distributions
class uniform_distribution(common_continuous):

    # a (int/float): Start of range
    # b (int/float): End of range
    def __init__(self, given_variable_name, lower_bound, upper_bound, a, b):

        # Enforces a <= b
        assert a <= b, "a=%.4f > b=%.4f" % (a, b)

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.uniform.html
        # Based on "abeboparebop"'s answer on
        # https://stackoverflow.com/questions/44572109/what-are-the-arguments-for-scipy-stats-uniform
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=uniform(loc = a, scale = (b - a)))

        common_continuous.__init__(self, given_variable_name, "Uniform", ["a", "b"], [a, b],
            E, Var, lower_bound, upper_bound, probability)

        # Stores distribution parameters
        self.a = a
        self.b = b


    # Obtains a series of inner points
    def calculate_inner_points(self):

        # If the current interval is not within bounds, select points at random
        if not (check_within_interval(self.lower_bound, self.a, self.b, contains=True) or
                check_within_interval(self.upper_bound, self.a, self.b, contains=True)):
            return [random.uniform(self.lower_bound, self.upper_bound) for _ in range(0, num_inner_points)]
        # Otherwise, select points within the overlapped range and return them
        else:
            considered_range = get_overlapped_range_p_dist([self.lower_bound, self.upper_bound], [self.a, self.b])

        r_lower, r_upper = considered_range

        return [random.uniform(r_lower, r_upper) for an_inner_point in range(0, num_inner_points)]



# Normal (Gaussian) distributions
class normal_distribution(common_continuous):

    # μ (int/float): Expectationn
    # σ (int/float): Standard deviation
    def __init__(self, given_variable_name, lower_bound, upper_bound, μ, σ):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=norm(loc=μ, scale=σ))

        common_continuous.__init__(self, given_variable_name, "Normal", ["μ", "σ"], [μ, σ],
            E, Var, lower_bound, upper_bound, probability)

        # Stores distribution parameters
        self.μ = μ
        self.σ = σ


    # Obtains a series of inner points
    def calculate_inner_points(self):
        return inner_points_within_range(norm(loc=self.μ, scale=self.σ), [self.lower_bound, self.upper_bound])



# Beta distributions
class beta_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, α, β):

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=beta(α, β))

        common_continuous.__init__(self, given_variable_name, "Beta", ["α", "β"], [α, β],
            E, Var, lower_bound, upper_bound, probability)

        # Stores distribution parameters
        self.α = α
        self.β = β


    # Obtains a series of inner points
    def calculate_inner_points(self):

        # If the current interval is not within bounds, select points at random
        if not (check_within_interval(self.lower_bound, 0, 1, contains=True) or check_within_interval(self.upper_bound, 0, 1, contains=True)):
            return [random.uniform(self.lower_bound, self.upper_bound) for _ in range(0, num_inner_points)]
        # Otherwise, select points within the overlapped range and return them
        else:
            considered_range = get_overlapped_range_p_dist([self.lower_bound, self.upper_bound], [0, 1])

        r_lower, r_upper = considered_range

        return inner_points_within_range(beta(self.α, self.β), [self.lower_bound, self.upper_bound])



# Pareto distributions
class pareto_distribution(common_continuous):

    # α (int/float)
    # β (int/float)
    def __init__(self, given_variable_name, lower_bound, upper_bound, x_m, α):

        # Enforces real values
        # Based on https://en.wikipedia.org/wiki/Pareto_distribution
        assert x_m > 0, "x_m cannot be zero or below"
        assert α > 0, "α cannot be zero or below"

        # Distribution calculations completed using
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pareto.html
        # https://en.wikipedia.org/wiki/Pareto_distribution
        # https://towardsdatascience.com/generating-pareto-distribution-in-python-2c2f77f70dbf
        probability, E, Var = get_PR_E_Var(ab=get_integral_points(lower_bound, upper_bound), cdist=pareto(α, scale=x_m))

        common_continuous.__init__(self, given_variable_name, "Pareto", ["x_m", "α"], [x_m, α],
            E, Var, lower_bound, upper_bound, probability)

        # Stores distribution parameters
        self.x_m = x_m
        self.α   = α


    # Obtains a series of inner points
    def calculate_inner_points(self):

        # If the current interval is not within bounds, select points at random
        if self.upper_bound < self.x_m:
            return [random.uniform(self.lower_bound, self.upper_bound) for _ in range(0, num_inner_points)]
        # Otherwise, select points within the overlapped range and return them
        else:
            considered_range = get_overlapped_range_p_dist([self.lower_bound, self.upper_bound], [self.x_m, np.inf])

        r_lower, r_upper = considered_range

        return inner_points_within_range(pareto(self.α, scale=self.x_m), [self.lower_bound, self.upper_bound])



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
        Var += ((b - a)/6)*(V_f_a + 4*V_f_ab_2 + V_f_b)

    Var -= E**2


    # Divides the result by the probability to make it accurate
    E   /= probability
    Var /= probability**2

    return [probability, E, Var]



# Checks (but not enforces) if a variable is contained within an interval
def check_within_interval(x, l, u, contains):
    if contains:
        return (l <= x) and (x <= u)
    else:
        return (l < x) and (x < u)



# Enforces that a value is within a lower and upper bound
# l <= u, not checked
def enforce_x_within_lu(x, l, u):

    assert(l <= x), "%.4f < %.4f" % (x, l)
    assert(x <= u), "%.4f > %.4f" % (x, u)



# Enforces that all the values in an array are within lower and upper bounds
# l <= u, checked
def enforce_array_within_lu(given_array, l, u):

    # Enforces that lower bound is below upper bound
    assert l <= u, "%.4f > %.4f" % (l, u)

    for x in given_array:
        enforce_x_within_lu(x, l, u)



# Divides a list of hyperparameters into distribution paremters themselves and sorted interval separation values
# The distribution parameters always appear first
# given_hp [(int), ...]
# num_p (int): Number of distribution parameters
def obtain_p_sv(given_hp, num_p):
    return [given_hp[:num_p], sorted(given_hp[num_p:])]



# Finds the overlapped interval between two ranges (R1, R2) (an overlap is assumed)
# R1 = [a (int | float), b (int | float)]: Range searched
# R2 = [a (int | float), b (int | float)]: Distribution range
# a <= b
def get_overlapped_range_p_dist(R1, R2):

    # Finds the smallest overlap
    if (R1[1] - R1[0]) > (R2[1] - R2[0]):
        L = R1 # Small range
        S = R2 # Large range
    else:
        L = R2
        S = R1

    a_R1, b_R1 = R1
    a_R2, b_R2 = R2

    # An overlap is assumed, the following configurations are possible (searched range as "-", distribution range as "+")
    if a_R1 < a_R2:

        # -------------
        #    +++++++++++++++++
        if b_R1 < b_R2:
            return [a_R2, b_R1]

        # -----------------------
        #    +++++++++++++++++
        else:
            return [a_R2, b_R2]

    else:

        #      -------------
        #    +++++++++++++++++
        if b_R1 < b_R2:
            return [a_R1, b_R1]

        #      ------------------
        #    +++++++++++++++++
        else:
            return [a_R1, b_R2]


# Obtains a series of inner points given a distribution and the range to search
# Assumed that points may occur anywhere within the distribution
# R = [a (int | float), b (int | float)]
def inner_points_within_range(cdist, R):

    # Gets the x, y range of valid points (Monte Carlo)
    x1, x2 = R

    y1 = 0

    # The max y is selected as the maximum psd obtained among a group of points
    y2 = -1 # Placeholder

    x_to_select_from = np.linspace(x1, x2, num_inner_points)

    for an_x in x_to_select_from:
        y2 = max(y2, cdist.pdf(an_x))


    # Keeps obtaining points until it finishes
    valid_points_so_far = 0
    P = []
    while valid_points_so_far < num_inner_points:

        xn = random.uniform(x1, x2)
        yn = random.uniform(y1, y2)

        if yn <= cdist.pdf(xn):
            P.append(xn)
            valid_points_so_far += 1

    return P


    # Obtains a series of inner points
    def calculate_inner_points(self):

        cdist=norm(loc=self.μ, scale=self.σ)

        # Gets the x, y range of valid points (Monte Carlo)
        x1, x2 = self.lower_bound, self.upper_bound
        y1, y2 = 0, max(cdist.pdf(x1), cdist.pdf(x2))


        # Keeps obtaining points until it finishes
        valid_points_so_far = 0
        P = []
        while valid_points_so_far < num_inner_points:

            xn = random.uniform(x1, x2)
            yn = random.uniform(y1, y2)

            if yn <= cdist.pdf(xn):
                P.append(xn)
                valid_points_so_far += 1

        return P