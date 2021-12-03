"""
SUMMARY

Parses the SimPPL language from .sppl file. Obtained from assignment file and based on https://lark-parser.readthedocs.io/en/latest/json_tutorial.html .
Modified following the instructor comment on MS Teams using https://lark-parser.readthedocs.io/en/latest/examples/turtle_dsl.html and
https://lark-parser.readthedocs.io/en/latest/examples/calc.html as examples.
Modified to process return as an expression, easier to parse. This will not cause any issues since it will be the last expression.
"""


import os

from lark import Lark


# Common lark from https://github.com/lark-parser/lark/blob/master/lark/grammars/common.lark

SimPPL_parser = Lark(r"""
    e: NAME
    | ESCAPED_STRING
    | SIGNED_NUMBER
    | and -> and_operation
    | or  -> or_operation
    | not -> not_operation
    | "true" -> true
    | "false" -> false
    | expect -> expectation_operation
    | var -> variance_operation
    | equal_check -> equal_operation
    | not_equal_check -> not_equal_operation
    | less_check -> less_operation
    | lt_check -> lt_operation
    | greater_check -> greater_operation
    | gt_check -> gt_operation


    and: ("(" "&&" e e ")"|"(" e "&&" e ")")
    or: ("(" "||" e e ")"|"(" e "||" e ")")
    not: "(" "!" e ")"

    expect: "E" "(" e ")"
    var : "Var" "(" e ")"

    equal_check:      ("(" "==" e e ")"|"(" e "==" e ")")
    not_equal_check:  ("(" "!=" e e ")"|"(" e "!=" e ")")
    less_check:       ("(" "<" e e ")"|"(" e "<" e ")")
    lt_check:         ("(" "<=" e e ")"|"(" e "<=" e ")")
    greater_check:    ("(" ">" e e ")"|"(" e ">" e ")")
    gt_check:         ("("" >=" e e ")"|"(" e ">=" e ")")



    s: assgn
    | flip
    | observe
    | ite
    | seq
    | ite_elseif
    | ite_complete
    | reject
    | marg
    | elimvar
    | print
    | bern
    | disc_num
    | disc_qual
    | d_uniform
    | d_gaussian
    | d_pareto
    | d_beta
    | d_uniform_num
    | d_gaussian_num
    | d_pareto_num
    | d_beta_num
    | show_circuit


    assgn: NAME "=" e
    flip: NAME ("∼"|"~") "flip" (SIGNED_NUMBER | "(" SIGNED_NUMBER ")")
    observe: "observe" e
    seq: s ";" s

    ite: "if" e "{" s ";"* "}" "else" "{" s ";"* "}"
    ite_elseif: "if" e "{" s ";"* "}" ["else" "if" e "{" s ";"* "}"]*
    ite_complete: "if" e "{" s ";"* "}" ["else" "if" e "{" s ";"* "}"]* "else" "{" s ";"* "}"

    reject: "reject" e
    marg: "marginalize" "(" e ["," e ]* ")"
    elimvar: "eliminate_variable" "(" NAME ["," NAME ]* ")"

    print: "print" "(" e ")"


    bern:      NAME ("∼"|"~") "bernoulli" "(" e ")"
    disc_num:  NAME ("∼"|"~") "discrete_numeric" "(" e "=" e ["," e "=" e ]* ")"
    disc_qual: NAME ("∼"|"~") "discrete_qualitative" "(" e "=" e ["," e "=" e ]* ")"

    d_uniform:  NAME ("∼"|"~") "uniform" "(" "a" "=" e "," "b" "=" e ["," e ]* ")"
    d_gaussian: NAME ("∼"|"~") ("gaussian"|"normal") "(" ("μ"|"mu") "=" e "," ("σ"|"sigma") "=" e ["," e ]* ")"
    d_pareto:   NAME ("∼"|"~") "pareto" "(" "x_m" "=" e "," ("α"|"alpha") "=" e ["," e ]* ")"
    d_beta:     NAME ("∼"|"~") "beta" "(" ("α"|"alpha") "=" e "," ("β"|"beta") "=" e ["," e ]* ")"

    d_uniform_num:  NAME ("∼"|"~") "uniform" "(" "a" "=" e "," "b" "=" e "," "n" "=" e ")"
    d_gaussian_num: NAME ("∼"|"~") ("gaussian"|"normal") "(" ("μ"|"mu") "=" e "," ("σ"|"sigma") "=" e "," "n" "=" e ")"
    d_pareto_num:   NAME ("∼"|"~") "pareto" "(" "x_m" "=" e "," ("α"|"alpha") "=" e "," "n" "=" e ")"
    d_beta_num:     NAME ("∼"|"~") "beta" "(" ("α"|"alpha") "=" e "," ("β"|"beta") "=" e "," "n" "=" e ")"


    show_circuit: "show_circuit" "(" ")"



    p: s ";" "return" e ";"*


        %import common.SIGNED_NUMBER
        %import common.WS
        %import common.CNAME -> NAME
        %ignore WS
        %import common.CPP_COMMENT
        %ignore CPP_COMMENT
        %import common.INT
        %import common.SIGNED_INT
        %import common.ESCAPED_STRING


    """, start="p")



# Transforms the parse tree into an organized structure, easier to work with
# Based on https://en.wikiversity.org/wiki/Python_Programming/Classes#Tutorials
class Program_structure(object):


    # "given_program_file_text": Text containing the program
    def __init__(self, given_program_file_text, program_filepath):
        # Stores the original parse tree in case it is needed in the future
        # https://lark-parser.readthedocs.io/en/latest/json_tutorial.html
        self.original_parsed_tree = SimPPL_parser.parse(given_program_file_text)

        # Obtains the instructions and output (return) trees
        self.instructions_tree = self.original_parsed_tree.children[0]
        self.output_tree = self.original_parsed_tree.children[1]
