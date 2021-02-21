# This is effectively half of a parser for C.
# It cannot parse, but can generate C code, which is the goal here.

from copy import deepcopy
from dataclasses import dataclass, field
from typing import List

# TC standard is 2 spaces
tab = "  "
def indent(text):
    return "\n".join([tab+line for line in text.split("\n") if line.strip() != ""])

########### Operators and Variables ##############
@dataclass
class Operator:
    symbol: str
    num_operands: int = 2
    def __str__(self):
        return self.symbol
    def __eq__(self, other):
        return self.symbol == other.symbol and self.num_operands == other.num_operands
    
# Just a container namespace
class Op:
    # Binary operators
    LT = Operator("<", 2)
    LE = Operator("<=", 2)
    GT = Operator(">", 2)
    GE = Operator(">=", 2)
    EQ = Operator("==", 2)
    NEQ = Operator("!=", 2)
    # Logical binary
    AND = Operator("&&", 2)
    OR = Operator("||", 2)

    ADD = Operator("+", 2)
    SUB = Operator("-", 2)
    MUL = Operator("*", 2)
    DIV = Operator("/", 2)
    PLUSEQ = Operator("+=", 2)
    MINUSEQ = Operator("-=", 2)
    TIMESEQ = Operator("*=", 2)
    DIVEQ = Operator("/=", 2)
    
    # Unary Operators
    NOT = Operator("!", 1)
    NEGATE = Operator("-", 1)

    PPLUS = Operator("++", 1)
    SSUB = Operator("--", 1)
    
    def __init__(self):
        raise ValueError("Cannot initialize Op")

class Value:
    def __init__(self):
        raise ValueError("Base Constructor of Value should not be called")

@dataclass
class Variable(Value):
    name : str
    typename : str = None
    
    def declare(self) -> str:
        if self.typename is None:
            raise ValueErorr("Variable {} can't have type None".format(self.name))
        return "{} {}".format(self.typename, self.name)
    def __str__(self):
        return str(self.name)
    def __eq__(self, other):
        # return self.fields() == other.fields()
        return self.name == other.name

def Int(name):
    return Variable(name, "int")
def Double(name):
    return Variable(name, "double")

# Easy operator
@dataclass
class Parens(Value):
    val: Value
    def __str__(self):
        return f"({self.val})"

@dataclass(init=False)
class Array(Value):
    dim : int
    def __init__(self, name : str, typename : str, dim : int=1):
        if typename is None:
            raise ValueError("Array cannot have None type")
        super(Array, self).__init__(name, typename)
        self.dim = dim
    def __str__(self):
        return self.name
    def declare(self) -> str:
        declaration = super(Array, self).declare()
        return declaration + "*"*self.dim
    def __eq__(self, other):
        return self.fields() == other.fields()

class Constant(Variable):
    def __init__(self, name : str):
        super(Constant, self).__init__(name)
Var = Variable # alias

zero = Constant("0")

@dataclass
class OpTree(Value):
    op : Operator
    left : Value
    right : Value = None
    def __str__(self):
        if self.right is None:
            print(self.op, type(self.op))
        assert (self.right is None) == (self.op.num_operands == 1)
        if self.right is None:
            return f"{self.op}{self.left}"
        return f"{self.left} {self.op} {self.right}"
Operation = OpTree # alias
def op_reduce(op, vals : List[Value]) -> OpTree:
    nvals = len(vals)
    if nvals == 0:
        raise ValueError("Cannot have 0 values in the operator")
    elif nvals == 1:
        return vals[0]
    
    if isinstance(op, Operator):
        op = [op]*(nvals-1)
    assert isinstance(op, list)
    new_val = OpTree(op[0], vals[0], vals[1])
    return op_reduce(op[1:], [new_val] + vals[2:])    
def Product(vals : List[Value]) -> OpTree:
    return op_reduce(Op.MUL, vals)
    
########## Conditions ############
    
# condition = var | unary | binary
@dataclass
class Condition(Value):
    var : Variable
    op : Operator = None
    var2 : Variable = None
    def __str__(self):
        if self.op is None: # just the variable
            return var.name
        elif self.var2 is None: # unary operator
            return "{}({})".format(self.op, self.var)
        else: # binary operator
            return "{} {} {}".format(self.var, self.op, self.var2)
def And(*conds : Value) -> OpTree:
    assert len(conds) > 1
    return op_reduce(Op.AND, list(conds))
def Or(*conds : Value) -> OpTree:
    assert len(conds) > 1
    return op_reduce(Op.OR, list(conds))

######### Statements ##############

class Statement:
    def __str__(self):
        return "{}{}".format("/* NOT IMPLEMENTED YET */")

class Empty(Statement):
    def __str__(self):
        return ""
    
# don't want this to be a subclass of statement
class Statements:
    def __init__(self, statements=None):
        if statements is None:
            self.statements = []
        elif isinstance(statements, Statements):
            self.statements = statements.statements
        elif isinstance(statements, list):
            self.statements = statements
        elif isinstance(statements, Statement):
            self.statements = [statements]
        else:
            raise ValueError("Statements passed {} of type {}".format(statements, type(statements)))
    def __str__(self):
        statements = []
        for statement in self.statements:
            s = str(statement).strip()
            is_container = isinstance(statement, Container)
            is_function = isinstance(statement, Function)
            is_string = isinstance(statement, str)
            is_macro = isinstance(statement, Macro)
            is_exception_type = is_container or is_string or is_macro
            function_declaration = is_function and statement.declaration
            extra_space = is_function and statement.newline
            if len(s) > 0 and (not is_exception_type or function_declaration):
                s += ";"
            if extra_space:
                s += "\n"
            statements.append(s)
        return "\n".join(statements)

@dataclass
class Call(Statement, Value): # function call
    name : str
    args : List[Value] = field(default_factory=list)
    def __str__(self):
        args = [str(a) for a in self.args]
        return "{}({})".format(self.name, ", ".join(args))

@dataclass(init=False)
class Element(Value):
    array : Array
    indices : List[Value]
    def __init__(self, array : Array, indices):
        self.array = array
        if isinstance(indices, Value):
            self.indices = [indices]
        else:
            self.indices = indices
        if len(self.indices) != self.array.dim:
            raise ValueError("Array {} has dim {} != {}".format(array.name, array.dim, len(self.indices)))
    def __str__(self):
        s = array.name
        for i in indices:
            s += "[{}]".format(i)
        return s
    
@dataclass
class Assignment(Statement): # Can technically be a Value but whatever
    var : Variable
    rhs : Value
    declare : bool = True
    # TODO: debug this
    def __str__(self):
        if self.declare:
            lhs = self.var.declare()
        else:
            lhs = self.var
        return "{} = {}".format(self.var, self.rhs)

@dataclass
class Update(Statement):
    var : Variable
    op : Operator
    val : Value = None
    
    def __str__(self):
        if self.val is None: # Unary operator
            return "{}{}".format(self.var, self.op)
        return "{} {} {}".format(self.var, self.op, self.val)

@dataclass
class Return(Statement):
    returned : Value = None
    def __str__(self):
        if self.returned is None:
            return "return"
        else:
            return "return {}".format(self.returned)

@dataclass
class Declaration(Statement):
    var : Variable
    def __str__(self):
        return self.var.declare()

######## Containers ##########

@dataclass
class Container(Statement):
    name : str
    args : List[Variable]
    body : Statements
    newline : bool = False
    
    def __str__(self):
        s = ""
        if self.args is None:
            s += "{} {{\n".format(self.name)
        else:
            s += "{}({}) {{\n".format(self.name, self.args)
        s += indent(str(self.body))
        s += "\n}"
        if self.newline:
            s += "\n"
        return s

class For(Container):
    def __init__(self, initial_statement, condition, update_statement, body):
        argstring = "{}; {}; {}".format(initial_statement, condition, update_statement)
        super(For, self).__init__("for ", argstring, body)
class While(Container):
    def __init__(self, condition, body):
        super(While, self).__init__("while ", condition, body)
class If(Container):
    def __init__(self, condition, body, has_else=False):
        name = ("else " if has_else else "") + "if "
        super(If, self).__init__(name, str(condition), body)
def Else(body : Statements) -> Container:
    return Container("else ", None, body)
class Function(Container):
    def __init__(self, t : str, name : str, args : List[Var], body : Statements, declaration=False):
        self.declaration = declaration
        argstring = ", ".join([a.declare() for a in args])
        name = "{} {}".format(t, name)
        super(Function, self).__init__(name, argstring, body, newline=True)
    def __str__(self):
        if self.declaration:
            return "{}({})".format(self.name, self.args)
        return super(Function, self).__str__()

########### Misc ##############

@dataclass
class Macro(Statement):
    name : str
    args : list = field(default_factory=list)
    def __str__(self):
        return "#{} {}".format(self.name, " ".join([str(a) for a in self.args]))

class Include(Macro):
    def __init__(self, filename, local=True):
        brackets = '""' if local else "<>"
        args = ["{}{}{}".format(brackets[0], filename, brackets[1])]
        super(Include, self).__init__("include", args)
class Define(Macro):
    def __init__(self, lhs, rhs=None):
        if rhs is None:
            args = [lhs]
        else:
            args = [lhs, rhs]
        super(Define, self).__init__("define", args)
Comment = str


############## Useful functions ###############

# Makes it easier to do the default case
def default_for(var : Var, start : Value, end : Value, body=None) -> For:
    if body is None:
        body = Statements()
    stat1 = Assignment(var, start)
    condition = Condition(var, Op.LT, end)
    stat2 = Update(var, Op.PPLUS)
    return For(stat1, condition, stat2, body)

def generate_c_file(body : List[Statement], disclaimer : str=None, includes : List[Include]=None, 
                    defines : List[Define]=None, guard : str=None) -> Statements:
        statements = []
        if disclaimer is not None:
            statements.append(disclaimer)
            statements.append(Empty())
        if guard:
            statements.append(Macro("ifndef", [guard]))
            statements.append(Define(guard))
            statements.append(Empty())
        if includes is not None:
            statements += includes
            statements.append(Empty())
        statements += body
        if guard:
            statements.append(Empty())
            statements.append(Macro("endif"))
        return Statements(statements)
