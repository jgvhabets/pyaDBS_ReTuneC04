"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
import numpy as np
import pandas as pd
# from dataclasses import dataclass
from timeflux.core.node import Node



class Compareinput(Node):
    def __init__(
        self,
        rel_power=True,
    ):
        if rel_power:
            self._threshold = .4
        print(f'Set threshold is: {self._threshold}')
        
    
    def update(self):
        input_value =  self.i.data.values[0, 0]
        # print('input value:', input_value, int(input_value > self._threshold))
        output = int(input_value > self._threshold)
        # print('EXC THRESH', output)

        # sets as pandas DataFrame
        self.o.data = pd.DataFrame(
            data=[[input_value, output]],
            columns=['IN', 'OUT'],
            index=self.i.data.index
        )
        print(self.o.data)