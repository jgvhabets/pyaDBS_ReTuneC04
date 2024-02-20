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
        experiment_name='',
        sfreq=None,
        seg_len_sec=.25,
    ):
        self.sfreq = sfreq
        self.seg_len_sec = seg_len_sec

        # load configurations
        self.marker_cfg = utils.get_config_settings(experiment_name)['biomarker']

        # check correctness of given coh_metric
        self.metric = self.marker_cfg['type']
        allowed_metrics = ['power', 'coh', 'squared_coh',
                           'icoh', 'abs_icoh' ]
        assert self.metric in allowed_metrics, (
            f'biomarker type (from: {experiment_name}) '
            f'not in {allowed_metrics}'
        )
        
        self.f_range = self.marker_cfg['freq_range']
        
    
    def update(self):
        # check input
        if not self.i.ready():
            return
        
        # copy the meta
        self.o = self.i

        # extract unknown sample freq and replace
        if not self.sfreq:
            self.sfreq = self.i.meta["rate"]
            self.nperseg = self.seg_len_sec * self.sfreq
        
        if self.metric == 'power':
            # take mean in case of multiple channels
            if self.i.data.shape[1] > 1:
                sig = np.mean(self.i.data, axis=1)
            else:
                sig = self.i.data.values.ravel()
                        
            assert type(sig[0]) == np.float64, (
                "raw signals have to np.float64"
            )

            # spectral decomposition
            freqs, values = welch(sig, fs=self.sfreq, nperseg=self.nperseg,)
        
        # select frequencies
        sel_values, sel_freqs = select_bandwidths(
            values=values, freqs=freqs,
            f_min=self.f_range[0], f_max=self.f_range[1]
        )
        value = np.mean(sel_values)
        # freq = int(np.mean(sel_freqs))

        # sets as pandas DataFrame
        self.o.data = pd.DataFrame(
            data=[[value]],
            columns=[f'{self.metric}: {self.f_range[0]}-{self.f_range[1]} Hz'],
            index=[datetime.now(tz=timezone.utc)]
        )
