import sys
import string
import re
from enum import Enum, auto
from dataclasses import dataclass
import itertools
from typing import Sequence

# All currently accepted tags
# tokenizer guaranteed to return one of these
token_tags = ["MULOP", "ADDOP", "NAME", "FUNCNAME", "NUMBER", "DOT", "COMMA", "LPAREN", "RPAREN"]

def is_valid_tag(t):
    return t.upper() in token_tags

TokenType = str # simple wrapper
@dataclass
class Token:
    tag : TokenType
    val : str

    def __str__(self):
        return self.val
    def __add__(self, other):
        assert isinstance(other, str)
        return Token(self.tag, self.val + other)
def print_token(token : Token):
    return f'({token.tag}, "{token.val}")'

number_regex = re.compile(r'[+-]?([0-9]+\.*[0-9]*|[0-9]*\.[0-9]+|[0-9]+)([eEdD][+-]?[0-9]+)?')
name_regex = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*')
funcname_regex = re.compile(r'[a-zA-Z_][a-zA-Z_0-9]*(?=\()') # like a name but before a paren
addop_regex = re.compile(r'[+\-]')
mulop_regex = re.compile(r'[*/]')
associations = [(addop_regex, "ADDOP"), (mulop_regex, "MULOP"), (funcname_regex, "FUNCNAME"), (name_regex, "NAME"), (number_regex, "NUMBER"), ('.', "DOT"), (',', "COMMA"), ('(', "LPAREN"), (')', "RPAREN")]

def tokenize(s) -> Sequence[Token]:
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
                    if t == "OPERATOR" and (len(tokens) == 0 or tokens[-1].tag not in ["FUNCNAME","NAME","RPAREN","NUMBER"]):
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
    for token in tokens:
        assert is_valid_tag(token.tag)
    return tokens

if __name__ == "__main__":
    s = "1.e-7 + 1. +4 (a + b) + f(a, b, c)"
    print(s)
    tokens = tokenize(s)
    print(', '.join([print_token(t) for t in tokens]))
    # print(get_string(tokens))
