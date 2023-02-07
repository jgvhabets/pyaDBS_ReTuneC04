"""
Creating dummy ephys-data for timeflux

to test run alone (WIN): python -m dummy.dummy_ephys
"""

# import public packages
from os.path import join
import pickle
import numpy as np
# from dataclasses import dataclass
from timeflux.core.node import Node
# from timeflux.helpers.testing import ReadData

# from os import getcwd, chdir

# define class which is imported as pickle
from utils import data_handle_helpers as dataHelpers
from utils.dummy_data_class import DummyData_Base

import random

class Testrandom(Node):
    def __init__(
        self,
        columns=5,
        rows_min=2,
        rows_max=10,
        value_min=0,
        value_max=9,
        names=None,
        seed=None,
    ):
        """Return random integers between value_min and value_max (inclusive)"""
        self._rows_min = rows_min
        self._rows_max = rows_max
        self._value_min = value_min
        self._value_max = value_max
        self._names = names
        self._columns = len(names) if names else columns
        random.seed(seed)
        np.random.seed(seed)

    def update(self):
        rows = random.randint(self._rows_min, self._rows_max)
        shape = (rows, self._columns)
        self.o.set(
            np.random.randint(self._value_min, self._value_max + 1, size=shape),
            names=self._names,
        )

"""
__init__ is performed only once at the start of the timeflux run,
update() is repeated at every repetition of the graph (frequency
indicated by the rate) 
"""
class Dummydata(Node):
    def __init__(
        self,
        winlen=250,
        datasource='stn',
        dummy_fname='dummy_data_class.P',
        seed=27,
    ):
        self._winlen = winlen
        self._datasource = datasource
        self._dummy_fname = dummy_fname
        self._dummy_path = join(
            dataHelpers.get_project_path('data'), 'dummy'
        )
        self._seed = seed

        from utils.dummy_data_class import DummyData_Base

        self._pickled_dummy = dataHelpers.load_pickled_class(
            join(self._dummy_path, self._dummy_fname)
        )
        self._dummy_data = np.array(getattr(
            self._pickled_dummy, self._datasource
        ))
        # print(vars(self._pickled_dummy).keys())
        self._dummy_name = getattr(
            self._pickled_dummy, f'{self._datasource}_name'
        )
        fs = self._pickled_dummy.fs
        print(f'Imported Dummy-Data ({datasource}) has fs: {fs} Hz')
        # # use either random selection
        # np.random.seed(seed)
        # or use increasing indices
        self._win_i = 0
        
    
    def update(self):
        # # use random index to chose window of dummy data
        # win_i = np.random.randint(
        #     0, self._dummy_data.shape[0] + 1, size=1
        # )[0]
        # use chronological windows of dummy data
        self._win_i += 1
        if self._win_i == self._dummy_data.shape[0]:
            self._win_i = 0
        win_i = self._win_i

        print(f'use window {win_i}')
        data_window = self._dummy_data[win_i, :self._winlen]
        chname = self._dummy_name

        # # original timestamps are not in dummy data
        # timestamps = [n * (1 / self._pickled_dummy.fs) for n in range(len(data_window))]
        
        # sets as pandas DataFrame
        self.o.set(
            data_window,
            # timestamps=timestamps,
            names=[chname],
        )




# if __name__ == '__main__':


#     dummy = Dummydata()

#     # print(dummy._dummy_data.shape)
#     # print(dummy._dummy_data[10, :8])

#     print(dummy.update())


