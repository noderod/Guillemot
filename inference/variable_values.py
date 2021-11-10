"""
SUMMARY

Keeps track of a variable value Implemented with this custom method instead of Boolean values to have more flexibility
Based on https://docs.python.org/3/library/enum.html .
"""


from enum import Enum



class variable_value(Enum):
    TRUE  = 1
    FALSE = 0
    INDETERMINATE = None



# Opposite values
# result of not operator
opposite_values = {
    variable_value.TRUE:variable_value.FALSE,
    variable_value.FALSE:variable_value.TRUE,
    variable_value.INDETERMINATE:variable_value.INDETERMINATE
}
