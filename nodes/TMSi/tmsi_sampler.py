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
import queue
# import serial

from timeflux.core.node import Node

from add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()

from TMSiSDK import tmsi_device, get_config, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, ChannelType, DeviceState
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable



from TMSiPlugins.external_devices.usb_ttl_device import USB_TTL_device, TTLError


class tmsiSampler(Node):
    """
    Class to connect and sample TMSi SAGA
    stream.
    """
    def __init__(
        self, TMSiDevice, COM_port, _QUEUE_SIZE = 1000
    ):
        """
        Parameters (required)
                TMSiDevice: USB TTL module is TMSi-device specific. Please enter the 
                               desired device in the parameters ("SAGA" or "APEX")
                COM_port: define the port on the computer where the TTL module was installed  

        """
        try:
            # Initialise the TMSi-SDK first before starting using it
            tmsi_device.initialize()
            
            # Execute a device discovery. This returns a list of device-objects for every discovered device.
            discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, DeviceInterfaceType.docked, 
                                                DeviceInterfaceType.usb)

            # Get the handle to the first discovered device.
            if (len(discoveryList) > 0):
                dev = discoveryList[0]
        except:
            raise ValueError('SAGA not detected in tmsiSampler()')      
        
        # only runs when tmsi_device.initialize resulted in an initialised device (dev)
        
        # Open a connection to the SAGA-system
        self.dev.open()

        # sanity check
        self.fs = dev.config.sample_rate
        print(f'detected sampling rate: {self.fs} Hz')

        # create queue and link it to SAGA device
        self.q_sample_sets = queue.Queue(maxsize=self._QUEUE_SIZE)  # if maxsize=0, queue is indefinite
        sample_data_server.registerConsumer(self.dev.id, self.q_sample_sets)
        print(f'TMSiSDK sample_data_server set for device: {self.dev.id}')


        

        self.dev.start_measurement()

        


    def update(self):

        print('update TMSI sampler')
        # get available samples from queue
        sampled = self.q_sample_sets.get()
        samples = np.array(sampled.samples)

        self.o.set(
            samples,
            name='tsmi_samples'
        )


    def close(self):
        
        self.dev.stop_measurement()
        self.dev.close()


if __name__ == '__main__':
    # execute
    tmsiSampler(TMSiDevice='SAGA', COM_port=1)


# def ACC_BIP_EXAMPLE():
#         # Set the sample rate of the AUX channels to 4000 Hz
#     dev.config.base_sample_rate = 4000
#     dev.config.set_sample_rate(ChannelType.AUX, 1)
#     dev.config.set_sample_rate(ChannelType.BIP, 1)
    
#     # Enable BIP 01, AUX 1-1, 1-2 and 1-3
#     AUX_list = [0,1,2]
#     BIP_list = [0]
    
#     # Retrieve all channels from the device and update which should be enabled
#     ch_list = dev.config.channels
    
#     # The counters are used to keep track of the number of AUX and BIP channels 
#     # that have been encountered while looping over the channel list
#     AUX_count = 0
#     BIP_count = 0
#     for idx, ch in enumerate(ch_list):
#         if (ch.type == ChannelType.AUX):
#             if AUX_count in AUX_list:
#                 ch.enabled = True
#             else:
#                 ch.enabled = False
#             AUX_count += 1
#         elif (ch.type == ChannelType.BIP):
#             if BIP_count in BIP_list:
#                 ch.enabled = True
#             else:
#                 ch.enabled = False
#             BIP_count += 1
#         else :
#             ch.enabled = False
#     dev.config.channels = ch_list
    
#     # Update sensor information
#     dev.update_sensors()


# Load the EEG channel set and configuration
# print("load EEG config")
# if dev.config.num_channels<64:
#     cfg = get_config("saga_config_EEG32")
# else:
#     cfg = get_config("saga_config_EEG64")
# dev.load_config(cfg)
