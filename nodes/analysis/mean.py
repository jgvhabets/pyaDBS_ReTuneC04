from timeflux.core.node import Node
from timeflux.core.registry import Registry
import numpy as np
import pandas as pd
from pylsl import local_clock
import utils.utils as utils


class Mean(Node):

    """Computes the arithmetic mean over the input data

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """

    def __init__(self, experiment_name='', config_field="mean"):

        # load configurations
        self.cfg = utils.get_config_settings(experiment_name)
        self.recording_channels = self.cfg['rec']['tmsi']['aDBS_channels']

        # initialize output class
        self.out = utils.output(rate=self.cfg['analysis'][config_field]['rate'], 
                                channels=self.recording_channels)

    def update(self):
        
        # Make sure we have a non-empty dataframe
        if self.i.ready():

            # print(f'mean -- data input at: {local_clock()}')

            # extract data
            data, package_id = utils.extract_data(self.i)

            # compute mean
            samples_mean = data.mean().values.reshape(1,-1)

            # get current timestamp
            timestamp_received = local_clock()
            # print(f'mean -- timestamp_received: {timestamp_received}')

            # Set as output 
            self.o.data, self.o.meta  = self.out.set(samples=samples_mean,
                                                     timestamp_received=timestamp_received,
                                                     package_id=package_id)

            # print(f'mean -- sent from mean at: {local_clock()}, package number {self.o.data["package_numbers"].iat[0]}, package id {self.o.data["package_ids"].iat[0]}')
