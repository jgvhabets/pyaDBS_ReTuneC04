"""
Perform DBS via AlphaOmega NeurOmega

to test run alone (WIN): python -m nodes.AO.AO_stim

chronic stim source: https://github.com/jlbusch/C04/blob/dev/stim_AO/stim_AO.m
"""

# import public packages
from pandas import DataFrame
# from dataclasses import dataclass
from timeflux.core.node import Node



class AO_stim(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
    ):
        # connect to AO
        ## TODO: find function on Labor PC; 'C:\CODE\Neuro Omega System SDK' 
        # macNO = 'F4:5E:AB:6B:6D:A1'
        # AO_DefaultStartConnection(macNO)
        # assert AO_IsConnected() == 1, (
        #     'Connection to NeuroOmega failed'
        # )
        # print('Connection to NeuroOmega established! :)')        
    
    def update(self):
        input_value =  self.i.data.values[0, 0]
        # print('input value:', input_value, int(input_value > self._threshold))
        output = int(input_value > self._threshold)
        # print('EXC THRESH', output)

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[input_value, output]],
            columns=['IN (biomarker)',
                     'OUT (aDBS trigger)'],
            index=self.i.data.index
        )
        # print(self.o.data)