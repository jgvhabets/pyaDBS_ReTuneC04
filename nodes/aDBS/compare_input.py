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

from pylsl import StreamInfo, StreamOutlet

class Compareinput(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
        experiment_name='',
    ):
        ### load configurations
        self.cfg = utils.get_config_settings(experiment_name)  # use given filename in graph .yml or default config_timeflux.json
        self.sfreq = None
        self._threshold = 'to_set'
        self.baseline_values = []  # to store the biomarkers for threshold decision

        self.marker_cfg = self.cfg['biomarker']
        
            
        # if self.marker_type == 'ACC':
        #     self.MARKER_FUNC = sig_vector_magn  # define dynamically which MARKER_CALC function to use
        # elif self.marker_type == 'power':
        #     self.marker_type = 'to_set'
        #     self._threshold = 'to_set'
        # else:
        #     raise ValueError(f'incorrect input_signal defined')

        print(f'...(init) threshold for {self.marker_cfg["type"]} set @ {self._threshold}')

        # Initialise the lsl-stream for raw data
        markers_streamInfo = StreamInfo(name="biomarker_log",
                                        type="Markers",
                                        channel_count=2,
                                        channel_format="string")
        self.biomarker_outlet = StreamOutlet(markers_streamInfo)
        # as first push, send selected channel names for saving
        t = datetime.now(tz=timezone.utc)
        self.biomarker_outlet.push_sample([f'biomarker type: {self.marker_cfg["type"]}',
                                           f'stream outlet init at clock: {str(t)}'])  # include time
        
    
    def update(self):
        
        # skip when no input
        if not self.i.ready():
            return

        if not self.sfreq:
            self.sfreq = self.i.meta["rate"]
            # calc n required samples for baseline threshold (1 sample = 1 epoch)
            self.base_samples = (self.marker_cfg['baseline_duration_sec']
                                 / self.marker_cfg['epoch_length_sec'])
        
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
            OUTPUT = float(value > self._threshold)
            print(f'...compare input: {value} vs {self._threshold} -> {OUTPUT}')

            t = datetime.now(tz=timezone.utc)
            self.biomarker_outlet.push_sample(
                [f'marker compared: {value}',
                 f'time: {str(t)}'])  # include time

            # sets as pandas DataFrame
            self.o.data = DataFrame(
                data=[[OUTPUT]],
                columns=['biomarker_compare',],
                index=[datetime.now(tz=timezone.utc)]
            )
    

    def set_default_empty_output(self):
        input_value = 0
        output = -99
        out_index = 0

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[output]],
            columns=['biomarker_output'],
            timestamps=[datetime.now(tz=timezone.utc)],
        )

    def define_threshold(self,):
        # add new sample(s)
        self.baseline_values.append([self.i.data.values[0]])
        print(f'...input shape (def threshold): {self.i.data.values.shape}')

        print(f'...defining THRESHOLD (n baseline values: {len(self.baseline_values)}'
              f' out of {self.base_samples})')

        if len(self.baseline_values) > self.base_samples:
            
            # calculate baseline  # TODO vary with baselining function
            self._threshold = np.mean(self.baseline_values)

            self._threshold = np.percentile(self.baseline_values, 75)

            print(f'\n....ACC THRESHOLD SET AT {self._threshold}')
            
            # send LSL markers
            t = datetime.now(tz=timezone.utc)
            self.biomarker_outlet.push_sample(
                [f'baseline values: {str(self.baseline_values)}',
                 f'time: {str(t)}'])  # include time
            t = datetime.now(tz=timezone.utc)
            self.biomarker_outlet.push_sample(
                [f'threshold set: {self._threshold}',
                 f'time: {str(t)}'])