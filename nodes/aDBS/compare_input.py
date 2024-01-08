"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from pandas import DataFrame
import numpy as np
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
        sfreq: int = 4000,
    ):
        if input_signal == 'stn_beta':
            self._threshold = .5
        elif input_signal == 'beta_coherence':
            self._threshold = .6
        elif input_signal == 'acc_movement':
            self._threshold = 'ACC_to_set'

        else:
            raise ValueError(f'incorrect input_signal defined')

        self.sfreq = sfreq

        print(f'Set threshold for {input_signal}'
              f' is set @ {self._threshold} (sampling at {self.sfreq} Hz)')
        
    
    def update(self):
        # temporary solution for None type input
        if self.i.data == None:
            print('no input data received')
            self.set_default_empty_output()


        # define ACC-threshold over 5 seconds of rest
        if isinstance(self._threshold, str):
            if self._threshold == 'ACC_to_set...':
                baseline_arr = self.i.data.values.ravel()
                setattr(self, '_threshold', 'ACC_setting')
                print('...still defining ACC threshold')
                self.set_default_empty_output()

            elif self._threshold == 'ACC_seting...':
                new_samples = self.i.data.values.ravel()
                baseline_arr = np.concatenate([baseline_arr, new_samples])
                # calculate baseline on 5 seconds
                if len(baseline_arr) < 5 * self.sfreq:
                    print(f'...still defining ACC threshold (baseline size: {len(baseline_arr)})')
                    self.set_default_empty_output()
                    
                else:
                    vector_magn = np.sqrt(baseline_arr ** 2)
                    setattr(self, '_threshold', vector_magn)
                    print(f'\n....ACC THRESHOLD SET AT {self._threshold}')
                    self.set_default_empty_output()
        
        # if threshold is set
        else:
            # get input values out of "i"
            input_value =  self.i.data.values[0, 0]
            # calculate sign vector magn
            if self.input_signal == 'ACC_movement':
                input_value = np.sqrt(input_value.ravel() ** 2)
            # compare calculated input signal
            output = int(input_value > self._threshold)
            out_index = self.i.data.index
            # PM: update with real-time timestamp?
            
            # print('input value:', input_value, int(input_value > self._threshold))

            # sets as pandas DataFrame
            self.o.data = DataFrame(
                data=[[output]],
                columns=['STIM'],
                index=out_index
            )
            # print(self.o.data)
    

    def set_default_empty_output(self):
        input_value = 0
        output = 0
        out_index = 0

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[output]],
            columns=['OUT (aDBS trigger)'],
            index=out_index
        )