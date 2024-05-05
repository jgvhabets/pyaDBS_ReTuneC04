from timeflux.core.node import Node
import pandas as pd
import utils.utils as utils
import os
import mne
from timeflux.helpers.handler import terminate_windows

class Save_mne(Node):

    """Imports 

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """

    def __init__(self, config_path=''):

        # load configurations
        self.cfg = utils.get_config_settings(
            folder_filename=os.path.basename(config_path),
            configs_folder=os.path.dirname(config_path)
            )
        
        # create info object
        self.info = mne.create_info(
            ch_names=self.cfg["rec"]["tmsi"]["aDBS_channel_bipolar"],
            sfreq=self.cfg["analysis"]["mean"]["rate"],
            ch_types="eeg"
            )
        
        # init data container
        self.data_all = pd.DataFrame()

        # set save path
        self.save_path = os.path.join(os.path.dirname(self.cfg["cal"]["path"]), "real_time_data_" + self.cfg["gen"]["condition_name"] + "_raw.fif")

        # misc
        self.saved = False

    def update(self):
        
        # loop through numbered import ports
        for iteration, port in enumerate(list(self.ports.values())):

            # Make sure we have a non-empty dataframe
            if port.ready():

                # extract data
                data, package_id = utils.extract_data(port)

                # append data
                self.data_all = pd.concat([self.data_all, data])

        # Empty port list will only come in once all input data has been processed. That's
        # the time to save the data
        if len(self.ports) == 0 and self.saved == False:
            
            # Generate mne raw array from data processed with timeflux
            calibration_real_time_power = mne.io.RawArray(data=self.data_all.values.T, info=self.info)
            
            # save data
            calibration_real_time_power.save(
                self.save_path,
                overwrite=True
                )
            
            # quit timeflux
            terminate_windows()

            self.saved = True
            