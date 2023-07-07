"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from pandas import DataFrame
# from dataclasses import dataclass
from timeflux.core.node import Node



class Compareinput(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
        input_signal=None,
    ):
        if input_signal == 'stn_beta':
            self._threshold = .5
        elif input_signal == 'beta_coherence':
            self._threshold = .6
        else:
            raise ValueError(f'incorrect input_signal defined')

        print(f'Set threshold for {input_signal}'
              f' is set @ {self._threshold}')
        
    
    def update(self):
        # temporary solution for None type input
        if self.i.data == None:
            input_value = 0
            output = 0
            out_index = 0

        else:

            input_value =  self.i.data.values[0, 0]
            # print('input value:', input_value, int(input_value > self._threshold))
            output = int(input_value > self._threshold)
            out_index = self.i.data.index

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[input_value, output]],
            columns=['IN (biomarker)',
                     'OUT (aDBS trigger)'],
            index=out_index
        )
        # print(self.o.data)