"""
Functions to help calculating spectral Features
"""

def select_bandwidths(
    values, freqs, f_min, f_max
):
    """
    Select specific frequencies in PSD
    or coherence outcomes
    Inputs:
        - values: array with values, can be one
            or two-dimensional (containing)
            different windows
        - freqs: corresponding array with frequecies
        - f_min (float): lower cut-off of
            frequencies to select
        - f_max (float): higher cut-off of
            frequencies to select
    
    Returns:
        - values: 1- or 2-d array with spectral values
        - freqs: 1d-array with corresponding frequencies
    """
    sel = [f_min <= f <= f_max for f in freqs]

    if len(values.shape) == 1:

        values = values[sel]
    
    elif len(values.shape) == 2:

        if values.shape[1] != len(freqs):

            values = values.T

        values = values[:, sel]
    
    freqs = freqs[sel]

    return values, freqs