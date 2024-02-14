"""
timeflux Node for power calculation
"""

# import public packages
from timeflux.core.node import Node
import numpy as np
from scipy.signal import periodogram
from utils.spectral_helpers import select_bandwidths
import utils.utils as utils
from pylsl import local_clock

class Power(Node):
    
    def __init__(self, config_filename='config.json'):
        
        # load configuration
        self.cfg = utils.get_config_settings(config_filename)
        self.power_cfg = self.cfg["analysis"]["power"]

        # set parameters for power calculation        
        self._fmin = self.power_cfg["f_band_min"]
        self._fmax = self.power_cfg["f_band_max"]

        # initialize output class
        self.out = utils.output(rate=self.cfg['analysis']['power']['rate'], 
                                channels=self.cfg['rec']['tmsi']['aDBS_channels'])      
        
    def update(self):

        # Make sure input data is available
        if self.i.ready():

            # Extract data
            data, package_id = utils.extract_data(self.i)

            # Make sure data does not contain NaNs
            if data.notna().all().iat[0]:

                # Compute PSD
                freqs, psd = periodogram(data, fs=self.i.meta["rate"], detrend=False, axis=0)
            
                # Select frequencies of interest
                sel_psd, _ = select_bandwidths(
                    values=psd, freqs=freqs,
                    f_min=self._fmin, f_max=self._fmax
                )

                # Average over frequencies of interest
                mean_psd = np.mean(sel_psd).reshape(1,-1)

            # if it contains NaNs, return NaN as power value
            else:

                mean_psd = np.array([np.nan]).reshape(1,-1)

            # get current timestamp
            timestamp_received = local_clock()

            # Set output
            self.o.data, self.o.meta  = self.out.set(samples=mean_psd,
                                                     timestamp_received=timestamp_received,
                                                     package_id=package_id)
