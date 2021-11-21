"""
SUMMARY

Keeps track of a variable value implemented with this custom method instead of Boolean values to have more flexibility.
Designed to be sued solely as the result of logical operators and not full variables by themselves.
Based on https://docs.python.org/3/library/enum.html .
"""


from enum import Enum



class logical_value(Enum):
    TRUE  = 1
    FALSE = 0



# Opposite values
# result of not operator
opposite_values = {
    logical_value.TRUE:logical_value.FALSE,
    logical_value.FALSE:logical_value.TRUE
}
