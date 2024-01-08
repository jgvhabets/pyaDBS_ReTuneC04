"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from pandas import DataFrame
import numpy as np
# from dataclasses import dataclass
from timeflux.core.node import Node

from nodes.TMSi.tmsi_utils import sig_vector_magn

class Compareinput(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
        input_signal=None,
        sfreq: int = 4000,
    ):
        if input_signal == 'stn_beta':
            self._threshold = .5
        elif input_signal == 'beta_coherence':
            self._threshold = .6
        elif input_signal == 'acc_movement':
            self._threshold = 'ACC_to_set'
            self.MARKER_FUNC = sig_vector_magn  # define dynamically which MARKER_CALC function to use  

        else:
            raise ValueError(f'incorrect input_signal defined')

        self.sfreq = sfreq

        print(f'Set threshold for {input_signal}'
              f' is set @ {self._threshold} (sampling at {self.sfreq} Hz)')
        
    
    def update(self):
        # print(f'\nCOMPARE DATA INPUT is type: {type(self.i.data)}')
        # print(f'content:\n{self.i.data}')
        
        # temporary solution for None type input
        if not isinstance(self.i.data, DataFrame):
            print('no input data received ("i.data" is not DataFrame)')
            self.set_default_empty_output()

        
        # recognize threshold to set on string type
        elif isinstance(self._threshold, str):

            # define ACC-threshold over 5 seconds of rest
            if self._threshold == 'ACC_to_set':
                print('START SETTING THRESHOLD ACC')
                self.baseline_arr = self.i.data.values[:, 0]  # possibly select input data by column name
                setattr(self, '_threshold', 'ACC_setting')
                print('...defining ACC threshold')
                self.set_default_empty_output()

            elif self._threshold == 'ACC_setting':
                new_samples = self.i.data.values[:, 0]
                self.baseline_arr = np.concatenate([self.baseline_arr, new_samples])
                # calculate baseline on 5 seconds
                if len(self.baseline_arr) < 5 * self.sfreq:
                    print(f'...still defining ACC threshold (baseline size: {len(self.baseline_arr)})')
                    self.set_default_empty_output()
                    
                else:
                    thresh = self.MARKER_FUNC(self.baseline_arr)
                    setattr(self, '_threshold', thresh)
                    print(f'\n....ACC THRESHOLD SET AT {self._threshold}')
                    self.set_default_empty_output()
        
        # if threshold is set and input is not None
        else:
            # get input values out of "i"
            input_sig =  self.i.data.values[:, 0]
            # calculate marker based on input_sig
            marker_value = self.MARKER_FUNC(input_sig)
            # compare calculated input signal
            output = int(marker_value > self._threshold)
            out_index = [self.i.data.index[-1]]
            # PM: update with real-time timestamp?
            print(f'THRESH: {self._threshold}, MARKER: {marker_value}, DECISION: {output} (idx: {out_index})')
            
            # sets as pandas DataFrame
            self.o.data = DataFrame(
                data=[[output]],
                columns=['STIM'],
                index=out_index
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