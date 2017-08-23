"""Simple encoding and decoding routines to convert between index triples such
as (i,j,k), [i,j,k] and a single integer.  That single integer may be used
efficiently as a key in dictionaries, for example.

This implementation uses a simple decimal scheme. Bit operations would likely be
somewhat faster, however, Python integers seem to lack the classical/low-level
sign bit which is essential.
"""


# numbers are encoded by addition to 'offset'
offset = 5000
# once encoded, numbers are shifted by multiplication with 'base'
base = 10000
bbase = base * base


# NOTE: Attempts to implement encode_triple() using NumPy array notation
# turned out to produce much slower code.


def encode_triple(triple):
    """Convert an index triple to a single integer."""
    i_enc = (offset + triple[0]) * bbase
    j_enc = (offset + triple[1]) * base
    k_enc = (offset + triple[2])
    return i_enc + j_enc + k_enc


def encode_indices(i, j, k):
    """Convert indices i,j,k to a single integer."""
    return encode_triple((i, j, k))


def decode_indices(value):
    """Convert a single integer to an index triple."""
    i = value // bbase - offset
    j = (value % bbase) // base - offset
    k = (value % base) - offset
    return (i, j, k)
