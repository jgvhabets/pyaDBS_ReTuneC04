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

    def __init__(self, config_path='', config_field="mean"):

        # load configurations
        self.cfg = utils.get_config_settings(config_path)
        self.recording_channels = self.cfg['rec']['tmsi']['aDBS_channel_bipolar']

        # initialize output class
        self.out = utils.output(rate=self.cfg['analysis'][config_field]['rate'], 
                                channels=self.recording_channels)

    def update(self):
        
        # loop through numbered import ports
        for iteration, port in enumerate(list(self.ports.values())):

            # Make sure we have a non-empty dataframe
            if port.ready():

                # self.logger.info(f'mean -- data input at: {local_clock()}')

                # extract data
                data, package_id = utils.extract_data(port)

                # compute mean
                samples_mean = data.mean().values.reshape(1,-1)

                # get current timestamp
                timestamp_received = local_clock()
                # print(f'mean -- timestamp_received: {timestamp_received}')

                # Set as output
                output_port = getattr(self, f"o_{iteration+1}")
                output_port.data, output_port.meta  = self.out.set(samples=samples_mean,
                                                        timestamp_received=timestamp_received,
                                                        package_id=package_id)

                # self.logger.info(f'mean -- sent from mean at: {local_clock()}, package number {self.o.data["package_numbers"].iat[0]}, package id {self.o.data["package_ids"].iat[0]}')
