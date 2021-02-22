# NOTE: Should only need to import:  print_integral, generate_integrals
# Implementation of recursive scheme in 
# S. Obara, A. Saika. J. Chem. Phys. 84, 3963 (1986); https://doi.org/10.1063/1.450106

import sympy as sym
from sympy.printing.c import C99CodePrinter # sympy.printing.c in some versions of sympy
from typing import Sequence, Tuple

# This module uses the naming convention and data types in gaussians
import gaussians # for utility functions
from gaussians import L, N, ABC # for clear types everywhere
from metacode import Value # for type signature
from parser import generate_value

# Symbols
Z = sym.symbols('Z', integer=False) # not sure if integer=False is necessary anymore
# These are shorthand in the paper and in terachem
# GA is just G - A, where A is the center of one of the Gaussians and G is a
#   weighted average of the three Gaussian centers.
GA = sym.symbols('GAx GAy GAz') # a list of three symbols for three_body_integral() to be clean.
GB = sym.symbols('GBx GBy GBz')
GC = sym.symbols('GCx GCy GCz')
GX = (GA, GB, GC) # Convenient list of all the symbols

# Helper function for three_body_integral() that lowers the angular momentum of an orbital
def succession(ja : int, i : int, abc : ABC) -> ABC:
    # convert to a list because tuples are immutable
    abc2 = [list(a) for a in abc]
    abc2[ja][i] -= 1
    return tuple(tuple(a) for a in abc2)

# This is just an implementation of the recursion relation in Equation 20 in the Obara, Saika paper.
# We use the variable Z = (2(zeta_A + zeta_B + zeta_C))^-1 for brevity.
# We also use (s|s|s)=1, so that integral needs to be calculated separately.
zero : N = (0,0,0) # might not need this
def three_body_integral(abc : ABC):
    assert all([len(a)==3 for a in abc]) # make sure input is formatted correctly
    # integral of 3 s orbitals
    if all([a == zero for a in abc]):
        return 1
    # only gets to this in some recursion successions. Returning 0 as a second base case is more elegant than filtering out in the recursive step.
    if any([any([ax < 0 for ax in a]) for a in abc]):
        return 0
    
#     result = sym.sympify(0) # starts with 0, so that we can add to it and then simplify at the very end.
    l_values = [sum(n) for n in abc] # list of total angular momenta of the three Gaussians
    jn = l_values.index(max(l_values)) # the index of the gaussian with the highest total n
    n = abc[jn] # the gaussian with the highest total n
    i = n.index(max(n)) # the index of n with the highest value (guaranteed to be nonzero) (e.g. x,y,z)
    abc2 = succession(jn, i, abc) # returns the gaussian with lowered indices
    result = GX[jn][i] * three_body_integral(abc2)
    for jm in range(3):
        result += Z * abc2[jm][i] * three_body_integral(succession(jm, i, abc2))
    return sym.simplify(result)

# This class simply prints
class IntegralPrinter(C99CodePrinter):
    def _print_Pow(self, expr):
        exp = expr.exp
        base = expr.base
        if exp.is_integer and int(exp) < 10:
            return "*".join([self._print(base)]*exp)
        else:
            return super(C99CodePrinter, self)._print_Pow(expr)
    def _print_Symbol(self, expr):
        s = super()._print_Symbol(expr)
        for x in "xyz":
            for A in "ABC":
                GA = f"G{A}"
                s = s.replace(f"{GA}{x}",f"{GA}.{x}")
        return s


# Abstract away the method by which the code is printed.
# No one should be calling printer.doprint() directly
printer = IntegralPrinter() # Singleton class
def to_code(expr) -> str:
    return printer.doprint(expr)


############### Only the following should need to be exposed ####################


# Calculates the algebraic expression for the desired TBI and converts to valid C code
# Really a helper function for the generate_integral*() functions and/or external callers
def print_integral(abc : ABC) -> str:
    integral = three_body_integral(abc)
    return to_code(integral)

# returns a list of all C formatted three body integrals with total angular momentum at most max_l
# This will take a while for L > 2, so progress is printed.
# @return list((str, str)) a list of integral function name and actual integral pairs
def generate_integrals(max_l : L) -> Sequence[Tuple[ABC, Value]]:
    orbitals = gaussians.generate_orbitals(max_l)
    n = len(orbitals)
    n2 = n*n
    n3 = n2*n
    # need all permutations of 3 orbitals, since order matters because of A,B,C being differently labeled centers.
    i = 0
    for abc in gaussians.generate_triples(max_l):
        if i % n2 == 0:
            print("{}%".format(100. * i/n3))
        integral = print_integral(abc)
        print(integral)
        integral = generate_value(integral)
        yield (abc, integral)
        i += 1


# Gets the gradients of all three body integrals (a|c|b) wrt GC
# GC is used because C is by convention the coordinate that the integral is evaluated at.
# In cases where we want the gradient of a 1e integral, C is likely a nuclear coordinate.
# TODO: Make sure we should be taking the derivative wrt C and not the others.
def generate_integral_gradients(max_l : L):
    for abc in gaussians.generate_triples(max_l):
        integral = three_body_integral(abc)
        derivs = []
        # Hardcoded to take the integral wrt C
        for GCx in GC:
            # d/dCx = -d/d(Gx-Cx)
            d = -sym.diff(integral, GCx)
            d = sym.simplify(d)
            derivs.append(to_code(d))
        yield tuple(derivs)
        
