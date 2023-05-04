"""
Establish connection with TMSi SAFA
device, to collect data samples from.

Extracted from https://gitlab.com/tmsi/tmsi-python-interface/
"""

# import sys
# from os import getcwd, chdir, listdir
# from os.path import pardir, join, dirname
import numpy as np
from pandas import DataFrame
# import serial

from timeflux.core.node import Node

from add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()

from TMSiPlugins.external_devices.usb_ttl_device import USB_TTL_device, TTLError


class tmsiSampler(Node):
    """
    Class to connect and sample TMSi SAGA
    stream.
    """
    def __init__(self, TMSiDevice, COM_port):
        """
        Parameters (required)
                TMSiDevice: USB TTL module is TMSi-device specific. Please enter the 
                               desired device in the parameters ("SAGA" or "APEX")
                COM_port: define the port on the computer where the TTL module was installed  

        """
        # Set up the blackbox TTL module. Throw an error if module was not found correctly
        try:
            # TMSiDevice is SAGA or APEX
            self.ttl_module = USB_TTL_device(TMSiDevice, com_port = COM_port)
            print('SAGA CONNECTED ?')
        except TTLError:
            raise TTLError("No trigger event cable is found")

    def update(self):

        print('update TMSI sampler')



if __name__ == '__main__':
    # execute
    tmsiSampler(TMSiDevice='SAGA', COM_port=1)