"""
Perform DBS via AlphaOmega NeurOmega

to test run alone (WIN): python -m nodes.AO.AO_stim_matlab

chronic stim source: https://github.com/jlbusch/C04/blob/dev/stim_AO/stim_AO.m
"""
# import public packages
import time
from pandas import DataFrame
from timeflux.core.node import Node

# import custom neuroomega matlab wrapper (credits: Richard Koehler) (located in REPO/packages/neuroomega_matlab)
import neuroomega_matlab as no
print('imported neuroomega_matlab')
# import repo functions
from AO_get_connection import (
    connect_AO,
    apply_and_stop_test_stim
)

class AO_stim(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self, macNO = 'F4:5E:AB:6B:6D:A1',
        AO_connection: str = 'matlab',
    ):
        # connect to AO
        self.no_engine = connect_AO(AO_connection=AO_connection,
                                    AO_MAC=macNO)

        # test stim start and stop
        try:
            apply_and_stop_test_stim(self.no_engine)

        except:
            closed = self.no_engine.AO_CloseConnection()
        
    
    def update(self):
        # is executed every time its activated by timeflux graph
        input_value =  self.i.data.values[0, 0]
        # print('input value:', input_value, int(input_value > self._threshold))
        output = int(input_value > self._threshold)
        # print('EXC THRESH', output)

        # TODO: aDBS decision making based on input signal
        # if stim should be switched on
        if True:
            self.no_engine.AO_DefaultStimulation(
                StimFreqRight=130,
                StimAmpRight_mA=0.5,
                StimFreqLeft=23,
                StimAmpLeft_mA=0.5,
                Duration_Sec=10.0,
            )
        
        # if stim should be switched off
        if True:
            self.no_engine.AO_DefaultStopStimulation()

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[input_value, output]],
            columns=['IN (biomarker)',
                     'OUT (aDBS trigger)'],
            index=self.i.data.index
        )
        # print(self.o.data)
    

    def close(self):
        closed = self.no_engine.AO_CloseConnection()
        print('closed NeuroOmega connection')



# try from command line
if __name__ == '__main__':
    print('command line run AO_stim_matlab class')
    AO_stim()