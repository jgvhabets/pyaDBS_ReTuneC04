"""
Helpers functions for signal processing
within timeflux workflow
"""
from os.path import join, dirname, exists
from os import getcwd
import pickle
import numpy as np
from dataclasses import dataclass


def get_project_path(
    subfolder: str = '',
):
    """
    Finds path of projectfolder, and
    subfolder if defined, on current machine
    For projectfolder path, no input is required.

    Input:
        - subfolder: data/code/figure to retrieve
            subfolder path
    """
    
    path = getcwd()

    repo_name = 'aDBS_C04'

    while_count = 0
    while path[-len(repo_name):] != repo_name:

        path = dirname(path)
        while_count += 1
        assert while_count < 10, 'Folder not found'
    
    if subfolder in ['data', 'code', 'figures', 'results']:

        return join(path, subfolder)
    
    elif len(subfolder) > 0:

        print('WARNING: incorrect subfolder')

    elif len(subfolder) == 0:
        return path


def get_repo_path(
    subfolder: str = '',
):
    """
    Finds path of projectfolder, and
    subfolder if defined, on current machine
    For projectfolder path, no input is required.

    Input:
        - subfolder: data/code/figure to retrieve
            subfolder path
    """
    
    path = getcwd()

    repo_name = 'pyaDBS_ReTuneC04'
    while path[-len(repo_name):] != repo_name:

        path = dirname(path)
    

from dummy.dummy_data_class import dummy_data

def load_pickled_class(path):

    with open(path, 'rb') as f:
        
        output = pickle.load(f)
        f.close()
    
    return output


