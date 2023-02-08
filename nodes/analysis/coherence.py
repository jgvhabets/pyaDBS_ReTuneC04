"""
timeflux Node for Coherence calculation
"""

# import public packages
import numpy as np
import pandas as pd
from scipy.signal import welch, csd 
from utils.spectral_helpers import select_bandwidths

from timeflux.core.node import Node



class Coherence(Node):
    def __init__(
        self,
        fs,
        nperseg=256,
        metric='squared_coh',
        f_band_min=14,
        f_band_max=20,
    ):
        self._fs = fs
        self._nperseg = nperseg

        # check correctness of given coh_metric
        allowed_metrics = [
            'coh', 'squared_coh', 'icoh', 'abs_icoh' 
        ]
        assert metric.lower() in allowed_metrics, print(
            f'incorrect coh_metric, should be in {allowed_metrics}')
        self._metric = metric.lower()

        self._fmin = f_band_min
        self._fmax = f_band_max
        
    
    def update(self):
        # test how i.data looks with two inputs
        # print(vars(self).keys())
        sig1 = self.i_sig1.data.values.ravel()
        sig2 = self.i_sig2.data.values.ravel()
        t1 = self.i_sig1.data.index.values[0]
        t2 = self.i_sig2.data.index.values[0]

        if t1 != t2: print('Coherence timings are not identical')
        
        assert type(sig1[0]) == np.float64, print(
            "raw signals have to np.float64"
        )

        # Coherence calculation
        freqs, S_xx = welch(sig1, fs=self._fs, nperseg=self._nperseg,)
        _, S_yy = welch(sig2, fs=self._fs, nperseg=self._nperseg,)
        _, S_xy = csd(sig1, sig2, fs=self._fs, nperseg=self._nperseg,)
        
        # take desired coherence metric
        coherency = S_xy / np.sqrt(S_xx * S_yy)
        if self._metric == 'coh':
            values = coherency.real  # take real part for coherence
        elif self._metric == 'squared_coh':
            values = S_xy.real**2 / (S_xx * S_yy)  # squared coherence, used by Gilron 2021
        elif self._metric == 'icoh':
            values = np.imag(coherency)  # take imaginary (pos and neg)
        elif self._metric == 'abs_icoh':
            values = abs(np.imag(coherency))  # take absolute value
        
        sel_values, sel_freqs = select_bandwidths(
            values=values, freqs=freqs,
            f_min=self._fmin, f_max=self._fmax
        )
        value = np.mean(sel_values)
        freq = int(np.mean(sel_freqs))

        # sets as pandas DataFrame
        self.o.data = pd.DataFrame(
            data=[[value]],
            columns=[f'{self._metric}_{freq}'],
            index=[t1]
        )
        # print(self.o.data)