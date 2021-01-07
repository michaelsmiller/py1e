import re
from integrals import generate_integrals
from parser import generate_value
from templates import apply_template, generate_disclaimer
# from gaussians import *
import gaussians as gauss

from metacode import *
import copy

# module globals
tab = "  " # TeraChem C standard

NFS = [int((l+1)*(l+2)/2) for l in range(10)] # number of functions at every angular momentum

GX = ["GA", "GB", "GC"]
integral_params = [Var(GA, "double3") for GA in GX] + [Var("Z", "double")]

######### File Writing ###############

def write_integral_files(h_filename, c_filename, disclaimer_text, max_l) -> None:
    c_body = []
    h_body = []
    h_body.append(Declaration(Var("double3", "struct")))
    for abc, integral in generate_integrals(max_l):
        func_name = "_".join([gauss.n_to_str(nj) for nj in abc])
        
        c_func = Function("double", func_name, integral_params, Statements(Return(integral)), declaration=False)
        c_body.append(c_func)
        
        h_func = copy.deepcopy(c_func)
        h_func.declaration = True
        h_func.newline = False
        h_body.append(h_func)
        
    disclaimer = generate_disclaimer(disclaimer_text)
    with open(h_filename, 'w') as file:
        ifdef_name = "__{}__".format(h_filename).replace(".", "_").upper()
        statements = generate_c_file(h_body, disclaimer=disclaimer, guard=ifdef_name)
        filestring = str(statements)
        file.write(filestring)
    print("Finished writing {0}".format(h_filename))
    with open(c_filename, 'w') as file:
        includes = [Include(h_filename), Include("vector_types.h", False)]
        statements = generate_c_file(c_body, disclaimer=disclaimer, includes=includes)
        filestring = str(statements)
        file.write(filestring)
    print("Finished writing {0}".format(c_filename))


######### UPDATE FUNCTION STUFF ########


# Note: This references the integrals, but without having to calculate them. It just calls the functions
#       relying on the convention of S_Px_Dxy(GA, GB, GC, Z) to describe the corresponding three-body integral

## These two functions are because in TeraChem you need to multiply in a factor of sqrt(3)/3
# to normalize dxx, dyy, and dzz. This is because of our choice of basis   -MM
def requires_dscale(n) -> bool:
    return sum(n) == 2 and max(n) == 2
def num_dscales(abc) -> int:
    return len([n for n in abc if requires_dscale(n)])

# alternative formatting of variables
def variable_name_separate(base, c, mi, mj) -> str:
    elements = "[I+{}][J+{}]".format(mi, mj)
    xyz = "x" * c[0] + "y" * c[1] + "z" * c[2]
    return "{0}{1}{2}".format(base, xyz, elements)
def variable_name_double3(base, c, mi, mj) -> str:
    if sum(c) == 1:
        # D[I+0][J+0].x
        return "{0}{2}.{1}".format(base, xyz, elements)
    elif sum(c) == 2:
        raise ValueError("xyz = {} not supported with array type DOUBLE3_ARRAYS".format(xyz))

def generate_updates(lc, II, JJ, dest):
    assert II <= JJ
    updates = []
    for mi in range(NFS[II]):
        for mj in range(NFS[JJ]):
            a = gauss.index_to_n(II, mi)
            b = gauss.index_to_n(JJ, mj)
            for mc in range(NFS[lc]):
                c = gauss.index_to_n(lc, mc)
                abc = (a,b,c)
                funcname = gauss.abc_to_funcname(abc)
                variable_name = variable_name_separate(dest, c, mi, mj)
                rhs = Call(funcname, integral_params)
                rhs = Product(["dscale"]*num_dscales(abc) + [rhs])
                statement = Update(variable_name, Op.PLUSEQ, rhs)
                updates.append(statement)
#                 updates.append("{0} += factor*{1}{2}({3});".format(variable_name, "dscale*"*num_dscales(abc), funcname, argstring))
    result = Statements(updates)
    return result


def generate_update_func(lc, dest, funcname, function_disclaimer, max_l):
    II_var = Var("II", "int")
    JJ_var = Var("JJ", "int")
    statements = []
    statements.append(Assignment(Var("dscale", "double"), "sqrt(3.)/3"))
    for II in range(max_l+1):
        for JJ in range(II, max_l+1):
            body = generate_updates(lc, II, JJ, dest)
#             body = tab + tab.join(body.splitlines(True))
#             statements.append(apply_template("case", II, JJ, body))
            condition = And([Condition(II_var, Op.EQ, Var(II)),  Condition(JJ_var, Op.EQ, Var(JJ))])
            statements.append(If(condition, body, has_else=II+JJ>0))
    
    body = Statements(statements)
    
    params = copy.deepcopy(integral_params)
    params += [Var("factor", "double"), II_var, JJ_var, Var("I","int"), Var("J","int")]
    params += [Var("{}{}".format(dest, x), "double **") for x in "xyz"]
    function = Function("void", "update{}".format(funcname), params, body)
    return str(function)
