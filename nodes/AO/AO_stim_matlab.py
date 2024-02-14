"""
Perform DBS via AlphaOmega NeurOmega

to test run alone (WIN): python -m nodes.AO.AO_stim_matlab

chronic stim source: https://github.com/jlbusch/C04/blob/dev/stim_AO/stim_AO.m
"""
# import public packages
import warnings
import pandas as pd
from timeflux.core.node import Node
from pylsl import local_clock
import numpy as np

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
        config_filename='config.json'
    ):
        # default start in false
        self.NO_CONNECTED = NO_CONNECTED
        
        # get configuration settings
        self.cfg = utils.get_config_settings(config_filename)

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

        # initialize output class
        self.out = utils.output(rate=self.cfg['analysis']['mean']['rate'], 
                                channels=self.stim_params.columns.tolist())        
    
    def update(self):
        # is executed every time its activated by timeflux graph
        # make sure we have a non-empty dataframe
        if self.i.ready():

            # print(f'AO_stim_matlab -- data input at: {local_clock()}') 

            # extract data
            data, package_id = utils.extract_data(self.i)

            # check if new stim params are different than current stim params      
            if self.has_new_stim_params(current_stim_params=self.stim_params, incoming_stim_params=data):

                # overwrite old stim params with new stim params
                self.stim_params = data

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

            # get current timestamp
            timestamp_received = local_clock()
            # print(f'AO_stim_matlab -- timestamp_received: {timestamp_received}')

            # Set output 
            self.o.data, self.o.meta  = self.out.set(samples=self.stim_params,
                                                     timestamp_received=timestamp_received,
                                                     package_id=package_id)
            
            # print(f'AO_stim_matlab -- sent from AO_stim_matlab at: {local_clock()}, package number {self.o.data["package_numbers"].iat[0]}, package id {self.o.data["package_ids"].iat[0]}')
        

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