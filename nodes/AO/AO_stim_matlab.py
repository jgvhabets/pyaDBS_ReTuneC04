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
from nodes.AO.AO_get_connection import (
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
        STIM_DURATION: float = 3.0,
        STIM_AMP_LEFT: float = 1.5,
        STIM_FREQ_LEFT: int = 130,
        STIM_AMP_RIGHT: float = 1.5,
        STIM_FREQ_RIGHT: int = 130,
    ):
        # connect to AO
        self.no_engine = connect_AO(AO_connection=AO_connection,
                                    AO_MAC=macNO)

        # test stim start and stop
        apply_and_stop_test_stim(self.no_engine)

        # except:
        #     print('\n### AO TEST STIM FAILED, NO closed...')
        #     closed = self.no_engine.AO_CloseConnection()
        
        self.STIM_DURATION = STIM_DURATION
        self.STIM_AMP_LEFT = STIM_AMP_LEFT
        self.STIM_FREQ_LEFT = STIM_FREQ_LEFT
        self.STIM_AMP_RIGHT = STIM_AMP_RIGHT
        self.STIM_FREQ_RIGHT = STIM_FREQ_RIGHT
        
    
    def update(self):
        # is executed every time its activated by timeflux graph
        # temporary solution for None type input
        if not isinstance(self.i.data, DataFrame):
            print('None input data received in (AO_stim_matlab): no stim change')
        
        else:
            STIM_INPUT =  self.i.data.values[0, 0]
            print(f'AO STIM input: {STIM_INPUT}')
                    
            # if stim should be switched on
            if STIM_INPUT == 1:
                print(f'\n...AO_STIM switched ON based on {STIM_INPUT}')
                self.no_engine.AO_DefaultStimulation(
                    self.STIM_FREQ_RIGHT,
                    self.STIM_AMP_RIGHT,
                    self.STIM_FREQ_LEFT,
                    self.STIM_AMP_LEFT,
                    self.STIM_DURATION,
                )  # always keep this order corr to DefaultStimulation function
                # set for output plotting
                stim_output = 1
            
            # if stim should be switched off
            elif STIM_INPUT == 0:
                print(f'\n...AO_STIM switched OFF based on {STIM_INPUT}')
                _ = self.no_engine.AO_DefaultStopStimulation()
                # set for output plotting
                stim_output = 0

            # sets as pandas DataFrame
            self.o.data = DataFrame(
                data=[[STIM_INPUT, stim_output]],
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