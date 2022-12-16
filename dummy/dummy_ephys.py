"""
Creating dummy ephys-data for timeflux
"""

# import public packages
from os.path import join, exists
import pickle
import numpy as np
from dataclasses import dataclass
from timeflux.core.node import Node

from os import getcwd, chdir

print(getcwd())
# define class which is imported as pickle
from utils.data_handle_helpers import get_project_path, load_pickled_class
from utils.dummy_data_class import DummyData_Base


@dataclass(init=True, repr=True,)
class DummyData(Node):
    winlen: int=250
    names=None
    seed=None
    datasource: str='stn'
    dummy_fname: str='dummy_data_class.P'
    
    def __post_init__(self,):

        dummy_path = join(get_project_path('data'), 'dummy')

        from utils.dummy_data_class import DummyData_Base

        self._pickled_dummy = load_pickled_class(
            join(dummy_path, self.dummy_fname)
        )
        self._dummy_data = getattr(
            self._pickled_dummy, self.datasource
        )

        self._names = self.names

    
    def update(self):
        
        data_window = self._dummy_data[10, 250:350]

        self.o.set(
            data_window,
            names=self._names,
        )


if __name__ == '__main__':


    dummy = DummyData()

    print(dummy._dummy_data.shape)