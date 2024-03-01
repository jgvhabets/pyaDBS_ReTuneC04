from timeflux.core.node import Node
from pylsl import local_clock
import utils.utils as utils
import os
import mne

class Data_import(Node):

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
        
        # load data to mne raw object
        self.calibration_data = mne.io.read_raw(fname=self.cfg["cal"]["path"])

        # select channels
        self.calibration_data.pick(self.cfg["rec"]["tmsi"]["aDBS_channels"])

        # initialize output class
        self.out = utils.output(rate=self.cfg['rec']['tmsi']['sampling_rate'], 
                                channels=self.cfg['rec']['tmsi']['aDBS_channels'])
        # set counter
        self.first_update = True

    def update(self):
        
        # Only execute once
        if self.first_update:

            # Set as output 
            self.o.data, self.o.meta  = self.out.set(
                samples=self.calibration_data.get_data().T,
                timestamp_received=local_clock(),
                )
                       
            self.first_update = False
