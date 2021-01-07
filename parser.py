import metacode as meta
from arpeggio import OneOrMore, ZeroOrMore, Optional, UnorderedGroup, PTNodeVisitor
import metacode as meta
from arpeggio import OneOrMore, ZeroOrMore, Optional, UnorderedGroup, PTNodeVisitor
from arpeggio import EOF, And, Not, RegExMatch as Reg, visit_parse_tree, text, isstr, Terminal
from arpeggio import NoMatch
from arpeggio.cleanpeg import ParserPEG

grammar = """
// Tokenizer
integer = r'[+-][0-9]+'
real = r'[+-]?([0-9]+\.[0-9]*|[0-9]*\.[0-9]+|[0-9]+)([eEdD][+-]?[0-9]+)?'
number = real / integer
name = r'[a-zA-Z_]+[a-zA-Z_0-9]*'
op = '*' / '/' / '+' / '-'

attribute = name '.' name
val = number / attribute / name 

parens = '(' expr ')'
product = factor (op factor)+
factor = parens / val

expr = product / parens / val
start = expr EOF
"""

parser = ParserPEG(grammar, "start", reduce_tree=False, skipws=True)

class ExpressionPrinter(PTNodeVisitor):
    def visit__default__(self, node, children):
        is_leaf = isinstance(node, Terminal)
        value = node.value
        print(f"{node.rule_name}: {value}")
        if not is_leaf:
            return "".join(children)
        if value not in "),(":
            return value
        return None
    def visit_operation(self, node, children):
        self.visit__default__(node, children)
        if len(children) == 2:
            return self.visit__default__(node, children)
        return " ".join(children)
    def visit_parens(self, node, children):
        self.visit__default__(node, children)
        assert len(children) == 1
        return f"({children[0]})"

class ValueGenerator(PTNodeVisitor):
    def visit__default__(self, node, children):
        if children is not None and len(children)==1:
            return children[0]
        if node.value not in "),(.":
            return node.value
    def visit_product(self, node, children):
        assert len(children) % 2 == 1
        while len(children) > 1:
            order = [children[i] for i in [1,0,2]]
            val = meta.OpTree(*order)
            children = [val] + children[3:]
        return children[0]
    def visit_op(self, node, children):
        return meta.Operator(node.value, 2)
    def visit_unary_op(self, node, children):
        return meta.Operator(node.value, 1)
    def visit_val(self, node, children):
        assert len(children) == 1
        child = children[0]
        if isinstance(child, meta.Value):
            return child
        return meta.Var(children[0])
    def visit_parens(self, node, children):
        return meta.Parens(children[0])
    def visit_attribute(self, node, children):
        # print(children)
        s = "{}.{}".format(*children)
        return meta.Var(s)
    
def get_print_tree(input_string : str) -> str:
    parse_tree = parser.parse(input_string)
    return visit_parse_tree(parse_tree, ExpressionPrinter())
def print_tree(input_string : str) -> None:
    print(get_print_tree(input_string))
    
def generate_value(input_string : str) -> meta.Value:
    parse_tree = parser.parse(input_string)
    return visit_parse_tree(parse_tree, ValueGenerator())

def run_interpreter(f):
    while True:
        input_string = input("\nExpr: ")
        f(input_string)
def try_print_tree(input_string):
    try:
        return get_print_tree(input_string)
    except RecursionError:
        print("Recursion Error")
    except NoMatch as e:
        print(f"No Match for '{input_string}'")
        print(e)

def print_thing(s):
    print(try_print_tree(s))
    print("")
def print_value(s):
    print(generate_value(s))
if __name__ == "__main__":
    run_interpreter(print_value);
    # S = ["(a + b) + c",
    #     "(a + b)",
    #     "a + (b + c)"]
    # trees = [try_print_tree(s) for s in S]
    # print(trees)

    # print(generate_value(s))
