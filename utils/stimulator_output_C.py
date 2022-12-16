"""
Stimulation output in aDBS, processing
biomarker into stimulation settings output
for AlphaOmega (python Class to use as 
timeflux-Node with C++ driving capacities)

cython docs: http://docs.cython.org/en/latest/src/tutorial/pure.html#static-typing
"""

# import public packages
import cython
import numpy as np
from timeflux.core.node import Node

# create cdef class (C-class)
@cython.cclass
class StimOutput(Node):
    cython.declare(a=cython.int, b=cython.double)
    c = cython.declare(cython.int, visibility='public')  # visiblity defaults to private, can also be readonly

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

# create cdef (C-function)
@cython.cfunc
def c_compare(a,b):
    """
    use to compare input bandpassed signal and
    preset stimulation-threshold
    """
    return a == b


# creates a cpdef function (C code callable at C level)
@cython.ccall
def drive_stimulator(
    stim_bool,
    stim_V=.20,
    stim_Hz=130,
    stim_us=60
):

    return stim_bool, stim_V, stim_Hz, stim_us
