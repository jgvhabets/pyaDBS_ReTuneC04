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

from nodes.TMSi.add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()

from TMSiSDK import tmsi_device, get_config, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, ChannelType, DeviceState
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable



from TMSiPlugins.external_devices.usb_ttl_device import USB_TTL_device, TTLError



class Tmsisampler(Node):
    """
    Class to connect and sample TMSi SAGA
    stream.

    Parameters (required)
        TMSiDevice: USB TTL module is TMSi-device specific. Please enter the 
                        desired device in the parameters ("SAGA" or "APEX")
        COM_port: define the port on the computer where the TTL module was installed 
    """
    def __init__(
        self, _QUEUE_SIZE = None, MIN_SAMPLE_SIZE: int = 256,
    ):
        try:
            # Initialise the TMSi-SDK first before starting using it
            tmsi_device.initialize()
            
            # Execute a device discovery. This returns a list of device-objects for every discovered device.
            discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, DeviceInterfaceType.docked, 
                                                DeviceInterfaceType.usb)

            # Get the handle to the first discovered device.
            if (len(discoveryList) > 0):
                self.dev = discoveryList[0]
        except:
            raise ValueError('SAGA not detected in tmsiSampler()')      
        
        # only runs when tmsi_device.initialize resulted in an initialised device (dev)
        
        try:
            # Open a connection to the SAGA-system
            self.dev.open()


            # sanity check
            self.fs = self.dev.config.sample_rate
            ch_list = self.dev.config.channels

            # save CONFIG as XML file and load (load and save configuration example)

            print(f'detected sampling rate: {self.fs} Hz')
            print(f'n-channels detected: {len(ch_list)}')

            self.ch_names = []  # manually create list with enabled channelnames

            for i_ch, ch in enumerate(ch_list):
                print(ch.type)

                if 'BIP' in ch.name:  # check ch.type (ch.type_is_aux) 
                    ch.enabled = True
                
                elif ch.type == ChannelType.AUX and ch.name in ['X', 'Y', 'Z']:
                    ch.enabled = True
                
                else:
                    ch.enabled = False
                
                # add enabled channel-names
                if ch.enabled:
                    print(f'channel # {i_ch}: {ch.name} ENABLED (type {ch.type})')   # ch.unit_name
                    self.ch_names.append(ch.name)
                else:
                    print(f'channel {ch.name} NOT enabled')

            self.dev.config.channels = ch_list
            self.dev.update_sensors()

            print(f'n-channels left: {len(self.dev.channels)}')
            print(f'enabled channel-names: {self.ch_names}')

            # create queue and link it to SAGA device
            self.q_sample_sets = queue.Queue(maxsize=_QUEUE_SIZE)  # if maxsize=0, queue is indefinite
            sample_data_server.registerConsumer(self.dev.id, self.q_sample_sets)
            # reshape sampler?
            print(f'TMSiSDK sample_data_server set for device: {self.dev.id}')


            self.sampling = True

            self.dev.start_measurement()

            self.count = 0

            self.sample_rate = self.dev.config.get_sample_rate(ChannelType.AUX)
            print(f'SMAPLING RATE: {self.sample_rate} Hz')

        except:
            print('__init__ within TMSiSampler failed')
            self.close()        


    def update(self):

        try:
            print(f'start update count {self.count}')
            sampled_arr = np.zeros((1, len(self.ch_names + 2)))

            while_count = 0

            while sampled_arr.shape[0] < self.MIN_SAMPLE_SIZE:
                print(f'in WHILE: shape sampled array: {sampled_arr.shape}')

                # print(f'q-size: {self.q_sample_sets.qsize()}')  # what is q-size?
                # get available samples from queue
                sampled = self.q_sample_sets.get()
                self.q_sample_sets.task_done()  # obligatory second line to get sampled samples
                # reshape samples that are given in uni-dimensional form
                new_samples = np.reshape(sampled.samples,
                                        (sampled.num_sample_sets,
                                        sampled.num_samples_per_sample_set),
                                        order='F')

                sampled_arr = np.concatenate([sampled_arr, new_samples], axis=0)

                while_count += 1

            print(f'shape sampled df to output.set: {sampled_arr.shape}')
            print(f'result of {while_count} while-iterations of sampling')

            samples = DataFrame(data=sampled_arr,
                                columns=self.ch_names + ['STATUS', 'COUNTER'])  # channels STATUS and COUNTER are always present


            self.o.set(
                samples,
                names=self.ch_names + ['STATUS', 'COUNTER'],
            )  # has to be dataframe

            # consider TMSi filewriter
            # # Initialise a file-writer class (Poly5-format) and state its file path
            # file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))


            self.count += 1

            if self.count > 50:
                print('count reached max')
                self.close()

        except:
            self.close()

    def close(self):
        # always run these, also in case of ctrl-c abort
        self.dev.stop_measurement()
        self.dev.close()


if __name__ == '__main__':
    # execute
    Tmsisampler()


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
