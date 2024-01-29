"""
Perform DBS via AlphaOmega NeurOmega

to test run alone (WIN): python -m nodes.AO.AO_stim_matlab

chronic stim source: https://github.com/jlbusch/C04/blob/dev/stim_AO/stim_AO.m
"""
# import public packages
import time
import warnings
import pandas as pd
from timeflux.core.node import Node
from pylsl import local_clock

# import custom neuroomega matlab wrapper (credits: Richard Koehler) (located in REPO/packages/neuroomega_matlab)
# import repo functions
from nodes.AO.AO_get_connection import (
    connect_AO,
    apply_and_stop_test_stim
)
import utils.utils as utils

class AO_stim(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self, macNO = 'F4:5E:AB:6B:6D:A1',
        AO_connection: str = 'matlab',
        NO_CONNECTED: bool = False,
    ):
        # default start in false
        self.NO_CONNECTED = NO_CONNECTED
        
        # get configuration settings
        self.cfg = utils.get_config_settings()

        # connect to AO
        if self.cfg['CONNECT_NEUROOMEGA']:
            self.no_engine = connect_AO(AO_connection=AO_connection,
                                        AO_MAC=macNO)

            # test stim start and stop
            apply_and_stop_test_stim(self.no_engine)

            self.NO_CONNECTED = True

        else:
            print('\n### Neuro-Omega not connected (according to configs.json)')

        # set initial stimulation parameters
        self.stim_params = pd.DataFrame(self.cfg['stim']['stim_params'], index=[0])
        
    
    def update(self):
        # is executed every time its activated by timeflux graph
        # make sure we have a non-empty dataframe
        if self.i.ready():

            # check if new stim params are different than current stim params      
            if self.has_new_stim_params(current_stim_params=self.stim_params, incoming_stim_params=self.i.data):

                # overwrite old stim params with new stim params
                self.stim_params = self.i.data

                # if neuroomega is connected update stim parameters on neuroomega
                if self.NO_CONNECTED:

                        self.no_engine.AO_DefaultStimulation(
                            self.stim_params['STIM_FREQ_RIGHT'],
                            self.stim_params['STIM_AMP_RIGHT'],
                            self.stim_params['STIM_FREQ_LEFT'],
                            self.stim_params['STIM_AMP_LEFT'],
                            self.stim_params['STIM_DURATION']
                        )  # always keep this order corr to DefaultStimulation function
            
                elif not self.NO_CONNECTED:
                    pass

            # sets as pandas DataFrame with current timestamp
            self.o.data = self.stim_params.set_index(pd.Index([local_clock()*1e9]))
        

    def close(self):
        closed = self.no_engine.AO_CloseConnection()
        print('closed NeuroOmega connection')

    def has_new_stim_params(self, current_stim_params, incoming_stim_params):
        
        new_stim_params = False

        for column in current_stim_params:
            if column in incoming_stim_params:
                if current_stim_params.iloc[0][column] != incoming_stim_params.iloc[0][column]:
                    new_stim_params = True
            else:
                warnings.warn(f"{column} of current stim params not found in new stim params")

        return new_stim_params



# try from command line
if __name__ == '__main__':
    print('command line run AO_stim_matlab class')
    AO_stim()