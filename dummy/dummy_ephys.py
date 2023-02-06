"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from os.path import join, exists
import pickle
import numpy as np
from dataclasses import dataclass
from timeflux.core.node import Node
from timeflux.helpers.testing import ReadData

from os import getcwd, chdir

# define class which is imported as pickle
from utils import data_handle_helpers as dataHelpers
from utils.dummy_data_class import DummyData_Base


@dataclass(init=True, repr=True,)
class DummyData(Node):
    winlen: int=250
    datasource: str='stn'
    dummy_fname: str='dummy_data_class.P'
    
    def __post_init__(self,):

        dummy_path = join(dataHelpers.get_project_path('data'), 'dummy')

        from utils.dummy_data_class import DummyData_Base

        self._pickled_dummy = dataHelpers.load_pickled_class(
            join(dummy_path, self.dummy_fname)
        )
        self._dummy_data = np.array(getattr(
            self._pickled_dummy, self.datasource
        ))

        # print(vars(self._pickled_dummy).keys())
        
        self._dummy_name = getattr(
            self._pickled_dummy, f'{self.datasource}_name'
        )

    
    def update(self):
        
        data_window = self._dummy_data[10, :8]
        chname = self._dummy_name
        timestamps = [n * (1 / self._pickled_dummy.fs) for n in range(len(data_window))]
        print(data_window)
        self.o.set(
            rows=data_window,
            timestamps=timestamps,
            # names=chname,
        )

if __name__ == '__main__':


    dummy = DummyData()

    # print(dummy._dummy_data.shape)
    # print(dummy._dummy_data[10, :8])

    print(dummy.update())


