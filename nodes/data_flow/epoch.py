from timeflux.core.node import Node
from pylsl import local_clock
import utils.utils as utils
from collections import deque
import pandas as pd
import numpy as np


class Epoch(Node):

    """Buffers incoming data and releases it in epochs

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """

    def __init__(self, config_filename='config.json'):

        # load configurations
        self.cfg = utils.get_config_settings(config_filename)
        self.recording_channels = self.cfg['rec']['tmsi']['aDBS_channels']
        self._win_size = utils.convert_time_samples(freq=self.cfg["rec"]["tmsi"]["sampling_rate"], time=self.cfg['data_flow']['epoch']['window_duration'])
        self._step_size = utils.convert_time_samples(freq=self.cfg["rec"]["tmsi"]["sampling_rate"], time=self.cfg['data_flow']['epoch']['step_duration'])

        # initialize output class
        self.out = utils.output(rate=self.cfg['data_flow']['epoch']['rate'], 
                                channels=self.recording_channels)
        
        # initialize buffer
        self.buffer = pd.DataFrame(np.nan, index=range(self._win_size-self._step_size), columns=self.recording_channels+["timestamps_received", "package_numbers", "package_ids"])


    def update(self):
        
        # Make sure we have a non-empty dataframe
        if self.i.ready():

            # print(f'epoch -- data input at: {local_clock()}')

            # add data to buffer
            self.buffer = pd.concat([self.buffer, self.i.data])

            # print(f'epoch -- buffer size: {self.buffer.shape[0]}')

            # Check if buffer has reached window size
            if self.buffer.shape[0] >= self._win_size:

                # print(f'epoch -- window size reached at: {local_clock()}')

                # extract data from buffer
                data_from_buffer = self.buffer.iloc[:self._win_size,]

                # update buffer
                self.buffer = self.buffer.iloc[self._step_size:,]

                # get current timestamp
                timestamp_received = local_clock()
                # print(f'epoch -- timestamp_received: {timestamp_received}')

                # Set as output 
                self.o.data, self.o.meta  = self.out.set(samples=data_from_buffer[self.recording_channels],
                                                         timestamp_received=timestamp_received)

                # print(f'epoch -- sent from epoch at: {local_clock()}, package number {self.o.data["package_numbers"].iat[0]}, package id {self.o.data["package_ids"].iat[0]}')
