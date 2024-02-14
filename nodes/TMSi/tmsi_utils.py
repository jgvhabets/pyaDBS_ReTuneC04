"""
Util functions for TMSi usage in timeflux
"""
from os import getcwd, listdir
from os.path import join, dirname, exists
import sys
import numpy as np
from itertools import compress

def add_tmsi_repo():
        
    # tmsi_repo_name = 'tmsi-python-interface'
    main_repo_name = 'pyaDBS_ReTuneC04'
    dir = getcwd()
    
    # set repo directory as dir
    for i in range(20):

        if not np.logical_or('packages' in listdir(dir),
                          dir.endswith(main_repo_name)):
                          
            dir = dirname(dir)
    packages_dir = join(dir, 'packages')

    assert exists(packages_dir), ('packages folder not found, '
                                  'check working directory of execution')

    # packages folder is found
    try:
        tmsi_foldername = [f for f in listdir(packages_dir)
                           if f.startswith('tmsi-python')][0]
    except:
        raise FileNotFoundError('tmsi-python folder not found in "repo/packages/"')
    
    tmsi_path = join(packages_dir, tmsi_foldername)

    assert exists(tmsi_path), f'non-existing tmsi-path: {tmsi_path}'
    
    sys.path.append(tmsi_path)

    print(f'added TMSi-packages PATH: {tmsi_path}')

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

def channel_selection(self):
    """
    Has two selection functions: 1) Select channels
    to save based on channel/data types, 2) select
    channels to use for aDBS biomarker creation

    Arguments:
        - based on 'recording_channel_types' and 
            'aDBS_channels' in tmsi-settings, config.json.
            channeltypes in list have to be the type-
            codes in the TMSI channel naming
    
    Returns:
        - updates TMSi channels in tmsi-sampler class (self)
        - add a boolean array to tmsi-sampler class (self)
            that select the aDBS biomarkers
    """
    
    self.ch_names= []
    print('include channel types for saving: '
            f'{self.tmsi_settings["recording_channel_types"]}')
    for channel in self.channels:
        # true if one of the codes is found in channel name
        if any([ch_code in channel.name
                for ch_code in self.tmsi_settings['recording_channel_types']]):
            channel.enabled = True
            self.ch_names.append(channel.name)

        else:
            channel.enabled = False
    # print(f'ch_names: {self.ch_names}')
    self.aDBS_channel_bool = [c in self.tmsi_settings["aDBS_channels"]
                                for c in self.ch_names]
    # print(f'adbs bool: {self.aDBS_channel_bool}')
    self.aDBS_ch_names = list(compress(self.ch_names, self.aDBS_channel_bool))
    # print(f'selected aDBS channel-names: {self.aDBS_ch_names}')
        
    assert sum(self.aDBS_channel_bool) > 0, 'no aDBS channels selected'
                    
def sig_vector_magn(sig, return_mean = True):

    svm = np.sqrt(sig ** 2)

    if return_mean: svm = np.nanmean(svm)

    return svm