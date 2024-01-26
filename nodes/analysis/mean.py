from timeflux.core.node import Node
from timeflux.core.registry import Registry
import numpy as np
import pandas as pd
from pylsl import local_clock


class Mean(Node):

    """Computes the arithmetic mean over the input data

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """


    def update(self):
        
        # Make sure we have a non-empty dataframe
        if self.i.ready():
            # copy input to output data
            self.o = self.i
            # compute the mean over input data and set as output with updated timestamp
            # local_clock() needs to be multiplied by 1e9 because for some weird reason, timeflux divides the timestamp by 1e9 
            # before sending it out to LSL. Otherwise timestamps would not be on the same magnitude as those provided by other APIs (e.g. TMSi-SDK)
            self.o.data = pd.DataFrame(self.i.data.mean().values.reshape(1,-1), 
                                       index=[local_clock()*1e9], 
                                       columns=self.i.data.columns)

