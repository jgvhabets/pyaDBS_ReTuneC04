"""
Modular timeflux Node to extract biomarker
"""

# import public packages
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from scipy.signal import welch, csd 
from utils.spectral_helpers import select_bandwidths

# import specific timeflux 
from timeflux.core.node import Node

# import custom functions
import utils.utils as utils


class Biomarker(Node):
    def __init__(
        self,
        config_path='',
    ):
        # load configurations
        self.marker_cfg = utils.get_config_settings(config_path)['biomarker']
        self.tmsi_cfg = utils.get_config_settings(config_path)['rec']['tmsi']

        self.sfreq = None
        # self.sfreq = self.tmsi_cfg['sampling_rate']  # take sample rate from input at first update
        
        # check correctness of given coh_metric
        self.metric = self.marker_cfg['type']
        allowed_metrics = ['power', 'coh', 'squared_coh',
                           'icoh', 'abs_icoh' ]
        assert self.metric in allowed_metrics, (
            f'biomarker type (from: {config_path}) '
            f'not in {allowed_metrics}'
        )
        
    
    def update(self):
        # check input
        if not self.i.ready(): return
        
        if self.i.meta["IGNORE"]: return
        
        # copy the meta
        self.o = self.i

        # extract unknown sample freq and replace
        if not self.sfreq:
            self.sfreq = self.i.meta["rate"]
            self.nperseg = self.marker_cfg['epoch_length_sec'] * self.sfreq
        
        if self.metric == 'power':
            # take mean in case of multiple (ephys) channels
            # consider to include SSD
            if self.i.data.shape[1] > 1:
                sig = np.mean(self.i.data, axis=1)
            else:
                sig = self.i.data.values.ravel()
                        
            assert type(sig[0]) == np.float64, (
                "raw signals have to np.float64"
            )

            # full spectral decomposition
            freqs, values = welch(sig, fs=self.sfreq, nperseg=self.nperseg,)
        
        # select frequencies
        sel_values, sel_freqs = select_bandwidths(
            values=values, freqs=freqs,
            f_min=self.marker_cfg['freq_range'][0],
            f_max=self.marker_cfg['freq_range'][1]
        )
        value = np.mean(sel_values)

        # sets as pandas DataFrame
        self.o.data = pd.DataFrame(
            data=[[value]],
            columns=[f'{self.metric}: {self.marker_cfg["freq_range"][0]}-{self.marker_cfg["freq_range"][1]} Hz'],
            index=[datetime.now(tz=timezone.utc)]
        )
