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
                

        # TODO: aDBS decision making based on input signal
        # if stim should be switched on
        if input_value == 1:
            print(f'\n...AO_STIM switched ON based on {input_value}')
            self.no_engine.AO_DefaultStimulation(
                StimFreqRight=130,
                StimAmpRight_mA=0.5,
                StimFreqLeft=23,
                StimAmpLeft_mA=0.5,
                Duration_Sec=10.0,
            )
            # set for output plotting
            stim_output = 1
        
        # if stim should be switched off
        elif input_value == 0:
            print(f'\n...AO_STIM switched OFF based on {input_value}')
            self.no_engine.AO_DefaultStopStimulation()
            # set for output plotting
            stim_output = 0

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[input_value, stim_output]],
            columns=['STIM-input',
                     'STIM-OUTPUT'],
            index=self.i.data.index
        )
    

    def close(self):
        closed = self.no_engine.AO_CloseConnection()
        print('closed NeuroOmega connection')



# try from command line
if __name__ == '__main__':
    print('command line run AO_stim_matlab class')
    AO_stim()