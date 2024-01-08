"""
Util functions for TMSi usage in timeflux
"""

import numpy as np


def correct_ACC_channelnames(channels, sides=['R', 'L']):
    """
    CREATE DOCSTRING
    """
    print(f'BEFORE NAMES CHANGING:', [ch.name for ch in channels])
    for AX in ['X', 'Y', 'Z']:
        first_side = True
        second_side = True
        
        if len([ch for ch in channels
                if ch.name == AX]) > 1:
        
            # correct XYZ to both sides
            for ch in channels:
                if ch.name == AX and first_side:
                    print(f'changing "{ch.name}" into "ACC{sides[0]}_{AX}"')
                    ch.name = f'ACC_{sides[0]}_{AX}'
                    first_side = False  # prevents more than one rename
                    continue

                if ch.name == AX and second_side:
                    print(f'changing "{ch.name}" into "ACC{sides[1]}_{AX}"')
                    ch.name = f'ACC_{sides[1]}_{AX}'
                    second_side = False
    
    return channels


def activate_channel_selection(self):
    """
    CREATE DOCSTRING
    """
    for channel in self.channels:
        if channel.name in self.cfg['rec']['tmsi']['recording_channels']:
            channel.enabled = True
        else:
            channel.enabled = False
                    

def sig_vector_magn(sig, return_mean = True):

    svm = np.sqrt(sig ** 2)

    if return_mean: svm = np.nanmean(svm)

    return svm