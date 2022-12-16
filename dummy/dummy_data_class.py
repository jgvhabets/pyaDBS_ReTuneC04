"""
Defining Class with Dummy data
to load via pickle
"""

# import packages
from dataclasses import dataclass
from numpy import ndarray


@dataclass(repr=True, init=True,)
class dummy_data:
    stn: ndarray
    stn_name: str
    ecog: ndarray
    ecog_name: str
    # fs: int  # TO ADD

    def __post_init__(self,):

        print('include Fs later in dummy_dataa')