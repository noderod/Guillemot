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
    | and -> and_operation
    | or  -> or_operation
    | not -> not_operation
    | "true" -> true
    | "false" -> false
    | expect -> expectation_operation

    and: ("(" "&&" e e ")"|"(" e "&&" e ")")
    or: ("(" "||" e e ")"|"(" e "||" e ")")
    not: "(" "!" e ")"

    expect: "E" "\[" NAME "\]"


    s: assgn
    | flip
    | observe
    | ite
    | seq
    | ite_elseif
    | ite_complete
    | block
    | marg
    | elim
    | bern
    | disc_num
    | disc_qual
    | d_uni
    | d_gau
    | d_pareto
    | d_beta


    assgn: NAME "=" (e|SIGNED_NUMBER|ESCAPED_STRING)
    flip: NAME ("∼"|"~") "flip" (NAME|SIGNED_NUMBER)
    observe: "observe" e
    seq: s ";" s
    ite: "if" e "{" s ";"* "}" "else" "{" s ";"* "}"


    ite_elseif: "if" e "{" s ";"* "}" ["elseif" e "{" s ";"* "}"]*
    ite_complete: "if" e "{" s ";"* "}" ["elseif" e "{" s ";"* "}"]* "else" "{" s ";"* "}"

    block: "block" e
    marg: "marginalize" e


    bern: NAME ("∼"|"~") "bernoulli" "(" (NAME|SIGNED_NUMBER) ")"
    disc_num: NAME ("∼"|"~") "discrete_numeric" "(" SIGNED_NUMBER "=" (NAME|SIGNED_NUMBER) ["," SIGNED_NUMBER "=" (NAME|SIGNED_NUMBER) ]* ")"
    disc_qual: NAME ("∼"|"~") "discrete_qualitative" "(" ESCAPED_STRING "=" (NAME|SIGNED_NUMBER) ["," ESCAPED_STRING "=" (NAME|SIGNED_NUMBER) ]* ")"

    d_uni: NAME ("∼"|"~") "uniform" "(" "a" "=" (NAME|SIGNED_NUMBER) "," "b" "=" (NAME|SIGNED_NUMBER) ["," (NAME|SIGNED_NUMBER) ]* ")"
    d_gau: NAME ("∼"|"~") ("gaussian"|"normal") "(" ("μ"|"mu") "=" (NAME|SIGNED_NUMBER) "," ("σ"|"sigma") "=" (NAME|SIGNED_NUMBER) ["," (NAME|SIGNED_NUMBER) ]* ")"

    d_pareto: NAME ("∼"|"~") "pareto" "(" "x_m" "=" (NAME|SIGNED_NUMBER) "," ("α"|"alpha") "=" (NAME|SIGNED_NUMBER) "," ["," (NAME|SIGNED_NUMBER) ]* ")"
    d_beta: NAME ("∼"|"~") "beta" "(" ("α"|"alpha") "=" (NAME|SIGNED_NUMBER) "," ("β"|"beta") "=" (NAME|SIGNED_NUMBER) ["," (NAME|SIGNED_NUMBER) ]* ")"



    p: s ";" "return" e


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
