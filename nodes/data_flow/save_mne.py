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
            ch_names=self.cfg["rec"]["tmsi"]["aDBS_channels"],
            sfreq=self.cfg["analysis"]["mean"]["rate"],
            ch_types="eeg"
            )
        
        # init data container
        self.data_all = pd.DataFrame()

        # set save path
        self.save_path = os.path.join(os.path.dirname(self.cfg["cal"]["path"]), "real_time_power_" + self.cfg["condition_name"] + ".fif")

        # misc
        self.saved = False

    def update(self):
        
        # Make sure we have a non-empty dataframe
        if self.i.ready():

            # extract data
            data, package_id = utils.extract_data(self.i)

            # append data
            self.data_all = pd.concat([self.data_all, data])

        else:
            
            if self.saved == False:

                calibration_real_time_power = mne.io.RawArray(data=self.data_all.values.T, info=self.info)
                
                calibration_real_time_power.save(
                    self.save_path,
                    overwrite=True
                    )
                
                terminate_windows()

                self.saved = True
            