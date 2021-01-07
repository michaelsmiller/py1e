from typing import Tuple, List, Sequence

# This module is just utility functions for converting between gaussians, elements of gaussians,
# groups of gaussians, and strings.


# global mapping of angular momentum quantum number to orbital name
orbital_names = ['s', 'p', 'd', 'f', 'g', 'h', 'i', 'j', 'k']

######## Conversions ########

# these functions are all a mapping from one domain to another.
# I'm annotating these domains/types as follows:
#     L = int              angular momentum quantum number
#     N = (L,L,L)          triple of quantum numbers, e.g. (0, 2, 1)
#     I = int              The total angular momentum of an orbital (sum of the components of N), like L for the whole orbital
#     ABC = (N,N,N)          A triple of orbitals to represent a three-body-integral (e.g. ((0,0,0), (0,1,1), (1,0,2)))

L = int
N = Tuple[L, L, L]
ABC = Tuple[N, N, N]

# L -> str
def l_to_str(l : L) -> str:
    return orbital_names[l]

# N -> str
def n_to_str(n : N) -> str:
    l = l_to_str(sum(n)).upper()
    suff = "x" * n[0] + "y" * n[1] + "z" * n[2]
    result = l + suff
    return result

# str -> N
def str_to_n(s : str) -> N:
    s = s.lower()
    prefix = s[0]
    suffix = s[1:]
    assert prefix in L
    assert len(suffix) == L.index(prefix)
    counts = [suffix.count(i) for i in "xyz"]
    return tuple(counts)

# N -> I
def n_to_index(n : N) -> L:
    l = sum(n)
    if l == 0:
        return 0
    elif l == 1:
        return n.index(max(n))
    elif l == 2:
        if max(n) == 1:
            return 2 - n.index(min(n))
        else: # max(n) == 2
            return n.index(max(n)) + 3
    else:
        raise ValueError("L value '{}' is not supported".format(l))

# total angular momentum doesn't have enough information to uniquely specify an orbital,
# so also need a magnetic quantum number (as long as d is the highest orbital, haha)
def index_to_n(l : L, m : L) -> N:
    temp = [0,0,0]
    if l == 0:
        pass
    elif l == 1:
        temp[m] = 1
    elif l == 2:
        if m < 3:
            hole = 2 - m
            temp = [1,1,1]
            temp[hole] = 0
        else:
            temp[m-3] = 2
    else:
        raise ValueError("L value '{}' is not supported".format(l))
    return tuple(temp)


# A -> str
def abc_to_funcname(abc : ABC) -> str:
    assert len(abc) == 3
    return "_".join([n_to_str(nj) for nj in abc])

# T -> A
def funcname_to_abc(name : str) -> ABC:
    abc = [str_to_n(a) for a in name.split('_')]
    abc = tuple(abc)
    assert len(abc) == 3
    return abc


############## Aggregate Functions ################


# generates all combinations of 3 Gaussian orbitals with angular momentum quantum numbers
# that add up to at MOST max_l.
# NOTE: This should not be a generator because having it sorted is nice and
#       the number of orbitals is only O(L^2), where L is the max total ang. momentum.
def generate_orbitals(max_l : L) -> List[N]:
    orbitals = []
    for x in range(max_l+1):
        for y in range(max_l+1 - x): # y is constrained by x (I don't think this constraint is required)
            for z in range(max_l+1 - x - y): # z is constrained by x and y
                n = (x,y,z)
                orbitals.append(n)
    # sort first by total angular momentum, then by components, in alphabetical x,y,z order
    orbitals.sort(key=lambda x: (sum(x), x))
    return orbitals

# In generator form for efficiency!
def generate_triples(max_l : L) -> Sequence[ABC]:
    orbitals : List[N] = generate_orbitals(max_l)
    for a in orbitals:
        for b in orbitals:
            for c in orbitals:
                yield (a,b,c)