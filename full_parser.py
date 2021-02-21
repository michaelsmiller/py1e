from __future__ import annotations # So that classes can include their definition
import sys
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple, Callable, Any

from lexer import Token, tokenize, token_tags, TokenType, is_valid_tag
import metacode as meta

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

attribute = D name
D = name dot

function = funcA funcB
funcA = funcname lparen
funcB = rparen
funcB = list rparen
list = expr listA
list = expr
listA = comma list

term = number
term = parens
term = product
term = function
term = attribute
term = name

expr = number
expr = parens
expr = product
expr = sum
expr = function
expr = attribute
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
all_rules = generate_rules(grammar)


@dataclass
class ParseNode:
    name : str
    start : int
    end : int
    children : Sequence[ParseNode] = field(default_factory=list)
ParseTree = ParseNode
def is_leaf(node : ParseNode) -> bool:
    return len(node.children) == 0

def parse_cnf(tokens, start, end, label, print_each=False):
    if print_each:
        print(f"{label} ?= {get_range(tokens, start, end)}")
    if is_valid_tag(label):
        if end - start == 1 and label.upper() == tokens[start].tag:
            yield ParseNode(label.upper(), start, end, [])
    else:
        # attempt to match all rules
        for rule in all_rules:
            # TODO: sort the rules.
            if rule.name == label:
                if is_unit(rule):
                    for child in parse_cnf(tokens, start, end, rule.left):
                        yield ParseNode(label, start, end, [child])
                elif end-start >= 2:
                    for p in range(start+1, end):
                        # print(f"{start}-{p}: {get_range(tokens, start, p)}")
                        # print(f"{p}-{end}: {get_range(tokens, p, end)}")
                        for lchild in parse_cnf(tokens, start, p, rule.left):
                            for rchild in parse_cnf(tokens, p, end, rule.right):
                                yield ParseNode(label, start, end, [lchild, rchild])

# takes in f(stream, node, children)
def traverse_tree_generator(f):
    def traverse_node(tokens, node : ParseNode):
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

def chain(values):
    new_values = []
    for v in values:
        if isinstance(v, list):
            new_values += v
        else:
            new_values.append(v)
    return new_values

default_type = "double"
def generate_AST_func(tokens, node, children):
    # children are already exactly how I want them
    # Children are either tokens or Value-like nodes already
    token = tokens[node.start]
    val = token.val
    tag = node.name
    children = chain(children)
    children = [child for child in children if child is not None]

    # Easy case
    if tag in ["list", "listA", "funcA", "funcB", "A", "B", "C", "D"]:
        return children

    # Terminal nodes are just tokens
    if len(children) == 0:
        assert len(node.children) == 0
        if tag in ["MULOP", "ADDOP"]:
            return meta.Operator(val, 2)
        elif tag in ["NAME", "FUNCNAME"]:
            return val
        elif tag == "NUMBER":
            return meta.Constant(val) # type shouldn't matter in metacode
        # don't want these
        elif tag in ["DOT", "COMMA", "LPAREN", "RPAREN"]:
            return None
        else:
            fail(f"Case for {token.tag} not included")
    elif len(children) == 1:
        child = children[0]
        if tag == "start":
            return child
        elif tag == "parens":
            return meta.Parens(child)
        elif tag in ["expr", "term"]:
            # Doing the variable creation here
            if isinstance(child, str):
                return meta.Var(child, default_type)
            else:
                return child
    
    if tag == "function":
        # children should be the funcname variable
        return meta.Call(children[0], children[1:])
    elif tag == "attribute":
        return meta.Var(".".join(children), default_type)
    elif tag in ["sum", "product"]:
        assert len(children) == 3
        return meta.Operation(children[1], children[0], children[2])
    else:
        fail(f"Couldn't parse {node.name}")
generate_AST = traverse_tree_generator(generate_AST_func)

def parse(s : str) -> ParseTree:
    tokens = tokenize(s)
    return next(parse_cnf(tokens, 0, len(tokens), "start"))

def generate_value(s : str) -> meta.Value:
    tree = parse(s)
    return generate_AST(tokens, tree)


if __name__ == "__main__":
    # for rule in all_rules:
    #     print(str(rule))

    s = "x() + a.b * 6"
    print(s)
    tokens = tokenize(s)
    print(tokens)

    print("\nStarting parse")
    # can do multiple parses
    # for tree in parse_cnf(tokens, 0, len(tokens), "start"):
    #     print(print_tree(tokens, tree))
    tree = next(parse_cnf(tokens, 0, len(tokens), "start"))
    # print(print_tree(tokens, tree))
    ast = generate_AST(tokens, tree)
    # ast = generate_value(s)
    print(str(ast))
