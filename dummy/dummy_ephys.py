"""
Creating dummy ephys-data for timeflux
"""

# import public packages
from os.path import join, dirname
import pickle
import numpy as np
from dataclasses import dataclass
from timeflux.core.node import Node



# define class which is imported as pickle
from utils.data_handle_helpers import (
    get_project_path,
    dummy_data,
    load_pickled_class
)


@dataclass(init=True, repr=True,)
class DummyData(Node):
    winlen: int=250
    names=None
    seed=None
    datasource: str='stn'
    dummy_fname: str='dummy_data_class.P'
    
    def __post_init__(self,):

        dummy_path = join(
            dirname(get_project_path()),
            'aDBS_C04', 'data', 'dummy')

        self._full_data = load_pickled_class(
            join(dummy_path, self.dummy_fname)
        )
        self._dummy_data_arr = getattr(
            self._full_data, self.datasource
        )

        self._names = self.names

    
    def update(self):
        
        data_window = self._dummy_data_arr[10, :]

        self.o.set(
            data_window,
            names=self._names,
        )
