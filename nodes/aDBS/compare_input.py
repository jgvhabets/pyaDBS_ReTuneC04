"""
comparing input -> currently sample biomarker and creating threshold

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from pandas import DataFrame
import numpy as np
from datetime import datetime, timezone

from timeflux.core.node import Node

import utils.utils as utils
from nodes.TMSi.tmsi_utils import sig_vector_magn

class Compareinput(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
        experiment_name='',
        sfreq=None,
    ):
        ### load configurations
        self.cfg = utils.get_config_settings(experiment_name)  # use given filename in graph .yml or default config_timeflux.json
        self.sfreq = None
        self._threshold = 'to_set'
        self.baseline_sigs = []

        self.marker_type = self.cfg['biomarker']['type']
        self.base_duration = self.cfg['biomarker']['baseline_duration_sec']
            
        # if self.marker_type == 'ACC':
        #     self.MARKER_FUNC = sig_vector_magn  # define dynamically which MARKER_CALC function to use
        # elif self.marker_type == 'power':
        #     self.marker_type = 'to_set'
        #     self._threshold = 'to_set'
        # else:
        #     raise ValueError(f'incorrect input_signal defined')

        print(f'Set threshold for {self.marker_type}'
              f' is set @ {self._threshold} (sampling at {self.sfreq} Hz)')
        
    
    def update(self):
        # print(f'\nCOMPARE DATA INPUT is type: {type(self.i.data)}')
        # print(f'content:\n{self.i.data}')

        #### TODO: give value to single_threshold script and load _threshold in single_threshoöld
        # autom save threhsold here!

        if not self.sfreq:
            self.sfreq = self.i.meta["rate"]
            self.base_samples = self.sfreq * self.base_duration
        
        # temporary solution for None type input
        if not self.i.ready():
            # self.set_default_empty_output()
            pass
        
        # recognize threshold to set on string type
        elif self._threshold == 'to_set':
            # define threshold
            self.define_threshold()
            # changes self._threshold if enough data is available
        
        # if threshold is set and input is not None
        else:
            # get input values out of "i"
            value = self.i.data.values[:, 0]
            
            # compare calculated input signal (done in aDBS script, e.g., single_threshold)
            
            # sets as pandas DataFrame
            self.o.set(
                [[value]],
                names=['input_value'],
                timestamps=[datetime.now(tz=timezone.utc)],
                meta={'rate': self.sfreq, 'threshold': self._threshold}
            )
    

    def set_default_empty_output(self):
        input_value = 0
        output = 0
        out_index = 0

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[output]],
            columns=['OUT (aDBS trigger)'],
            index=[out_index]
        )

    def define_threshold(self,):
        # add new sample(s)
        print('... SETTING THRESHOLD ACC')
        self.baseline_sigs.append([self.i.data.values[0]])
        
        if len(self.baseline_sigs) > self.base_samples:
            
            # calculate baseline  # TODO vary with baselining function
            self._threshold = np.mean(self.baseline_sigs)

            self._threshold = np.percentile(self.baseline_sigs, 75)

            print(f'\n....ACC THRESHOLD SET AT {self._threshold}')
            # TODO: create LSL stream and markers