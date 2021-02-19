from __future__ import annotations
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Sequence, Tuple, Callable, Any


from lexer import Token, tokenize, token_tags, TokenType, is_valid_tag
from metacode import *

class ParsingError(Exception):
    pass

def fail(s : str=None):
    if s is None:
        s = "Generic parsing error: fill in later"
    raise ParsingError(s)
def get_range(tokens, i, j):
    return ''.join([token.val for token in tokens[i:j]])

# TOKENS = number | name | ( | ) | . | , | operator | e

#########################################
#  Grammar (not left recursive I hope)  #
#########################################
# operation = number operator number
# start = operation epsilon

grammar="""
product = A term
A = term mulop

sum = B expr
B = expr addop

parens = C rparen
C = lparen expr

function = funcA funcB
funcA = name lparen
funcB = rparen
funcB = list rparen
list = expr listA
list = expr
listA = comma list

term = number
term = parens
term = product
term = function
term = name

expr = number
expr = parens
expr = product
expr = sum
expr = function
expr = name

start = expr
"""

@dataclass
class Rule:
    name : str
    left : str
    right : str = None

    def __str__(self):
        s = f"{self.name} -> {self.left}"
        if self.right is not None:
            s += f" {self.right}"
        return s
def is_unit(rule : Rule) -> bool:
    return rule.right is None
def is_token(rule : Rule) -> bool:
    return rule.left is None


# TODO: convert to a CNF grammar automatically
# Don't actually need the final step of not allowing tokens and nonterminals in the same rule
def generate_rules(grammar):
    rules = []
    terminal_rules = set([])
    for line in grammar.split("\n"):
        line = line.strip()
        if len(line) == 0:
            continue

        assert "=" in line
        split = line.split()
        assert len(split) >= 3
        rule_name = split[0]
        # if anything on the rhs is a token, need to change it and add another rule
        rhs = []
        for r in split[2:]:
            rhs.append(r)
        rules.append(Rule(rule_name, *rhs))
    return rules

# includes terminals
all_rules = generate_rules(grammar)
for rule in all_rules:
    print(str(rule))


@dataclass
class Node:
    name : str
    start : int
    end : int
    children : Sequence[Node] = field(default_factory=list)
ParseTree = Node
def is_leaf(node : Node) -> bool:
    return len(node.children) == 0

def parse_cnf(tokens, start, end, label, print_each=False):
    if print_each:
        print(f"{label} =? {get_range(tokens, start, end)}")
    if is_valid_tag(label):
        if end - start == 1 and label.upper() == tokens[start].tag:
            yield Node(label.upper(), start, end, [])
    else:
        # attempt to match all rules
        for rule in all_rules:
            if rule.name == label:
                if is_unit(rule):
                    for child in parse_cnf(tokens, start, end, rule.left):
                        yield Node(label, start, end, [child])
                elif end-start >= 2:
                    for p in range(start+1, end):
                        # print(f"{start}-{p}: {get_range(tokens, start, p)}")
                        # print(f"{p}-{end}: {get_range(tokens, p, end)}")
                        for lchild in parse_cnf(tokens, start, p, rule.left):
                            for rchild in parse_cnf(tokens, p, end, rule.right):
                                yield Node(label, start, end, [lchild, rchild])

# takes in f(stream, node, children)
def traverse_tree_generator(f):
    def traverse_node(tokens, node : Node):
        children = list([traverse_node(tokens, child) for child in node.children])
        return f(tokens, node, children)
    return traverse_node

def print_tree_func(tokens, node, children):
    s = ''
    s += f"{node.name} \"{''.join([token.val for token in tokens[node.start:node.end]])}\""
    if children != []:
        s += ":\n"
        for child in children:
            # adds spaces before
            child_string = "\n".join([f"  {line}" for line in child.split('\n')])
            s += child_string + "\n"
    s = s.strip()
    return s
print_tree = traverse_tree_generator(print_tree_func)


if __name__ == "__main__":
    s = "x+1+f(10, 11)"
    tokens = tokenize(s)
    print(tokens)

    print("\nStarting parse")
    for tree : ParseTree in parse_cnf(tokens, 0, len(tokens), "start"):
        print(print_tree(tokens, tree))
