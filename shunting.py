from metacode import *
import sys
import string
import re
from enum import Enum, auto
from dataclasses import dataclass
import itertools

class Type(Enum):
    NAME = auto()
    NUMBER = auto()
    OPEN_PAREN = auto()
    CLOSE_PAREN = auto()
    DOT = auto()
    COMMA = auto()
    OPERATOR = auto()

@dataclass
class Token:
    t : Type
    val : str

    def __str__(self):
        return self.val
    def __add__(self, other):
        assert isinstance(other, str)
        return Token(self.t, self.val + other)
def print_token(tok : Token):
    return (tok.t.name, tok.val)

number_regex = re.compile(r'[+-]?([0-9]+\.*[0-9]*|[0-9]*\.[0-9]+|[0-9]+)([eEdD][+-]?[0-9]+)?')
name_regex = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')
op_regex = re.compile(r'[+\-*/]')
associations = [(op_regex, Type.OPERATOR), (name_regex, Type.NAME), (number_regex, Type.NUMBER), ('.', Type.DOT), (',', Type.COMMA), ('(', Type.OPEN_PAREN), (')', Type.CLOSE_PAREN)]

def tokenize(s):
    # Treats word breaks as token boundaries
    # if " " in s:
    #     return list(itertools.chain.from_iterable([tokenize(w) for w in s.split()]))
    s = s.replace(" ", "")
    tokens = []
    i = 0
    while i < len(s):
        j = i
        for key, t in associations:
            if isinstance(key, str): # string literal match
                if s[i] == key:
                    tokens.append(Token(t, s[i]))
                    j = i+1
                    break
            else: # regex match
                match = re.match(key, s[i:])
                if match is not None:
                    match_string = match.group(0)
                    # Need to know whether +- is an operator or part of a number
                    prefilter = True
                    if t == Type.OPERATOR and (len(tokens) == 0 or tokens[-1].t not in [Type.NAME, Type.CLOSE_PAREN, Type.NUMBER]):
                        prefilter = False
                    if prefilter:
                        tokens.append(Token(t, match_string))
                        j = i + len(match_string)
                        break

        if j <= i:
            print(f"Couldn't match {s[i:]}")
            sys.exit(1)
        else:
            i = j
    return tokens


class AmountMod(Enum):
    One = auto()
    OneOrMore = auto()
    ZeroOrMore = auto()
    Sequence = auto()
def match_amount(amount, tokens, i):
    if amount == Amount.One:

def get_string(tokens):
    # return "|".join([t.val for t in tokens])
    return " ".join([t.val for t in tokens])


# TOKENS
# name, number, operation, (, ), ',', '.'

# GRAMMAR:
# expr = val
# val = function | number | var
# function = name '(' (val ',')* ')'
# var = name
# operation = val operator val

def find_closing(tokens, start, end=len(tokens)):
    balance = 1
    for i in range(start, end):
        if tokens[i].t == Type.OPEN_PAREN:
            balance += 1
        elif tokens[i].t == Type.CLOSE_PAREN:
            balance -= 1
        if balance == 0:
            return i
    print("Couldn't find right paren")
    sys.exit(1)
    
def parse_parens(tokens, start, end):
    if tokens[start].t != Type.OPEN_PAREN:
        return
    start = start + 1
    end = find_closing(tokens, start, end)
    for val, end1 in parse_val(tokens, start, end):
        if end == end1:
            return Parens(val), end+1
def parse_function(tokens, start, end):
    if tokens[start].t != Type.NAME or start <= end - 3:
        return
    funcname = tokens[start].val
    start += 1
    end = find_closing(tokens, start, end)
    vals = []
    if start != end:

def parse_list(tokens, start, end):
    for i in range(start+1, end-1):
        for val1, i in parse_val(tokens, start, i):
            

def parse_expr_help(tokens, i, min_precedence):
    token = tokens[i]
    
    
def parse_expr(tokens):
    for val, end in parse_val(tokens, 0):
        if end == len(tokens):
            return val

if __name__ == "__main__":
    s = "1.e-7 + 1. +4 (a + b) + f(a, b, c)"
    print(s)
    tokens = tokenize(s)
    print([print_token(t) for t in tokens])
    print(get_string(tokens))
