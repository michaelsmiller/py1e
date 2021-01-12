import re
from integrals import generate_integrals
from parser import generate_value
import gaussians as gauss
from gaussians import L, N, ABC # types

from metacode import *
import copy

# module globals
tab = "  " # TeraChem C standard

NFS = [int((l+1)*(l+2)/2) for l in range(10)] # number of functions at every angular momentum

GX = ["GA", "GB", "GC"]
integral_params = [Var(GA, "double3") for GA in GX] + [Var("Z", "double")]

######### File Writing ###############

# This cute function takes a block of text and creates a visually pleasing C-style
# comment block out of it.
def generate_disclaimer(text):
    N = 80
    buffer_length = 8 # This just looks good
    
    # derived
    chars_per_line = N - 2 - 2*buffer_length
    buffer = " "*buffer_length
    
    # The outputted disclaimer
    s = ""
    s += "/" + "*" * (N-1) + "\n" # first line
    s += "{0}{1}{0}\n".format("*", " "*(N-2)) # Empty line for vertical spacing
    
    text = text.replace('\n', ' ').strip()
    words = text.split()
#     assert all([len(w) <= buffer_length for w in words]) # makes sure no words or URLs are too long for a line
    counter = 0
    iw = 0
    while iw < len(words):
        counter += 1
        length = 0
        line = words[iw]
        if len(line) > chars_per_line:
            print('Warning: "{}" has length {}, which exceeds the allowed line length of {}'.format(line, len(line), chars_per_line))
        iw += 1
        for jw in range(iw, len(words)):
            w = words[jw]
            if len(line) + len(w) + 1 <= chars_per_line:
                line += " " + w
                iw += 1
            else:
                break

        if counter == 20:
            return
        num_extra_spaces = chars_per_line - len(line)
        left_spaces = " " * int(num_extra_spaces/2)
        right_spaces = " " * (int(num_extra_spaces/2) + num_extra_spaces % 2)
        line = "{0}{1}{2}".format(left_spaces, line, right_spaces)
        
        s += "{0}{1}{2}{1}{0}\n".format("*", buffer, line)
    
    s += "{0}{1}{0}\n".format("*", " "*(N-2)) # Empty line for vertical spacing
    s += "*" * (N-1) + "/\n" # last line
    return s
def write_integral_files(h_filename : str, c_filename : str, disclaimer_text : str, max_l : L) -> None:
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
def requires_dscale(n : L) -> bool:
    return sum(n) == 2 and max(n) == 2
def num_dscales(abc : ABC) -> int:
    return len([n for n in abc if requires_dscale(n)])

# alternative formatting of variables
def variable_name_separate(base, c : N, mi : L, mj : L) -> str:
    elements = "[I+{}][J+{}]".format(mi, mj)
    xyz = "x" * c[0] + "y" * c[1] + "z" * c[2]
    return "{0}{1}{2}".format(base, xyz, elements)
def variable_name_double3(base, c : N, mi : L, mj : L) -> str:
    if sum(c) == 1:
        # D[I+0][J+0].x
        return "{0}{2}.{1}".format(base, xyz, elements)
    elif sum(c) == 2:
        raise ValueError("xyz = {} not supported with array type DOUBLE3_ARRAYS".format(xyz))

def generate_updates(lc : L, II : L, JJ : L, dest : str):
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
    result = Statements(updates)
    return result

def generate_update_func(lc : L, dest : str, funcname : str, function_disclaimer : str, max_l : L):
    II_var = Var("II", "int")
    JJ_var = Var("JJ", "int")
    statements = []
    statements.append(Assignment(Var("dscale", "double"), "sqrt(3.)/3"))
    for II in range(max_l+1):
        for JJ in range(II, max_l+1):
            body = generate_updates(lc, II, JJ, dest)
            condition = And(Condition(II_var, Op.EQ, Var(II)), Condition(JJ_var, Op.EQ, Var(JJ)))
            statements.append(If(condition, body, has_else=II+JJ>0))
    body = Statements(statements)
    
    params = copy.deepcopy(integral_params)
    params += [Var("factor", "double"), II_var, JJ_var, Var("I","int"), Var("J","int")]
    params += [Var("{}{}".format(dest, x), "double **") for x in "xyz"]
    function = Function("void", f"update{funcname}", params, body)
    return str(function)
