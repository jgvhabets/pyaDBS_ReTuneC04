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
from datetime import datetime, timedelta, timezone
# import serial

from timeflux.core.node import Node

from nodes.TMSi.add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()

from TMSiSDK import tmsi_device, get_config, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, ChannelType, DeviceState
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable
from TMSiFileFormats.file_writer import FileWriter, FileFormat



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
        self, _QUEUE_SIZE = None, MIN_SAMPLE_SIZE_SEC: int = .01,
        use_LSL: bool = False,
    ):
        self.MIN_SAMPLE_SIZE_SEC = MIN_SAMPLE_SIZE_SEC
        self.use_LSL = use_LSL

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
            print('closing TMSi before connecting...')
            self.close()  # stops measurement and closes dev

                       
        try:
            # Open a connection to the SAGA-system
            self.dev.open()

            # sanity check
            self.sfreq = self.dev.config.sample_rate
            self.ch_list = self.dev.config.channels

            # save CONFIG as XML file and load (load and save configuration example)
            print(f'detected sampling rate: {self.sfreq} Hz')
            print(f'channels detected (n={len(self.ch_list)}): {[c.name for c in self.ch_list]}')
            print(f'MIN SAMPLE SIZE: {self.MIN_SAMPLE_SIZE_SEC} seconds')
            print(f'use LSL stream: {self.use_LSL}')

            self.ch_names = []  # manually create list with enabled channelnames
            X_right, Y_right, Z_right = False, False, False

            for i_ch, ch in enumerate(self.ch_list):

                # if 'BIP' in ch.name or ch.type == ChannelType.BIP:  # check ch.type (ch.type_is_aux) 
                #     ch.enabled = True
                # else:
                #     ch.enabled = False
                
                if ch.type == ChannelType.AUX and ch.name in ['X', 'Y', 'Z']:
                    ch.enabled = True
                
                else:
                    ch.enabled = False
                
                # rename enabled channel-names
                if ch.enabled:
                    print(f'channel # {i_ch}: {ch.name} ENABLED (type {ch.type})')   # ch.unit_name
                    # adjust X Y Z without side
                    if ch.name == 'X':
                        if X_right:
                            ch.name = 'X_L'
                        else:
                            ch.name = 'X_R'
                            X_right = True
                    elif ch.name == 'Y':
                        if Y_right:
                            ch.name = 'Y_L'
                        else:
                            ch.name = 'Y_R'
                            Y_right = True
                    elif ch.name == 'Z':
                        if Z_right:
                            ch.name = 'Z_L'
                        else:
                            ch.name = 'Z_R'
                            Z_right = True

                    self.ch_names.append(ch.name)
            
            # update configurations   
            self.dev.config.channels = self.ch_list
            self.dev.update_sensors()

            self.n_channels = len(self.dev.channels)
            print(f'channels left (n={self.n_channels}): {[ch.name for ch in self.dev.channels]}')
            print(f'enabled channel-names: {self.ch_names}')

            # self.CH_SEL['ACC_L'] = [c in ['X_L', 'Y_L', 'Z_L'] for c in self.ch_names] + [False, False]
            # self.CH_SEL['ACC_R'] = [c in ['X_R', 'Y_R', 'Z_R'] for c in self.ch_names] + [False, False]

            # create queue and link it to SAGA device
            self.q_sample_sets = queue.Queue(maxsize=_QUEUE_SIZE)  # if maxsize=0, queue is indefinite
            sample_data_server.registerConsumer(self.dev.id, self.q_sample_sets)

            # start sampling on tmsi
            self.sampling = True
            self.dev.start_measurement()

            self.count = 0

            if self.use_LSL:
                # Initialise the lsl-stream
                self.stream = FileWriter(FileFormat.lsl, "SAGA")
                # Pass the device information to the LSL stream.
                self.stream.open(self.dev)

        except:
            print('__init__ within TMSiSampler failed')
            # Close the file writer after GUI termination
            self.close()  # closes both dev.measurement and dev itself         


    def update(self):
        
        try:
            # Getting the current date and time
            dt_start = datetime.now(tz=timezone.utc)
            dt_start = dt_start.astimezone()
            
            # sampled_arr = np.zeros((1, len(self.dev_channels)))
            
            # get available samples from queue
            sampled = self.q_sample_sets.get()
            self.q_sample_sets.task_done()  # obligatory second line to get sampled samples
            sampled_arr = sampled.samples

            # while sampled_arr.shape[0] < (self.fs * self.MIN_SAMPLE_SIZE_SEC):
            while (len(sampled_arr) / self.n_channels) < (self.sfreq * self.MIN_SAMPLE_SIZE_SEC):
                # get available samples from queue
                sampled = self.q_sample_sets.get()
                self.q_sample_sets.task_done()  # obligatory second line to get sampled samples

                sampled_arr = np.concatenate(sampled_arr, sampled.samples)

            # # reshape samples that are given in uni-dimensional form
            # new_samples = np.reshape(sampled.samples,
            #                          (sampled.num_sample_sets,
            #                           sampled.num_samples_per_sample_set),
            #                           order='C')
            # reshape samples that are given in uni-dimensional form
            sampled_arr = np.reshape(sampled_arr,
                                     (len(sampled_arr) // sampled.num_samples_per_sample_set,
                                      sampled.num_samples_per_sample_set),
                                      order='C')

            # sampled_arr = np.concatenate([sampled_arr, new_samples], axis=0)

                # while_count += 1

            # get timestamps whenever buffer is ready to be outputted
            txdelta = timedelta(seconds=1 / self.sfreq)
            t_array = np.array([dt_start + (np.arange(sampled_arr.shape[0]) * txdelta)]).ravel()  # create timestamp list with timedelta of sampling freq, for correct shape

            t_stop = datetime.now(tz=timezone.utc)
            # print(f'time @ stop: {t_stop}, last time in df: {t_array[-1]}')
            # print(f'shape sampled df to output.set: {sampled_arr.shape}')
            # print(f'result of {while_count} while-iterations of sampling')

            samples = DataFrame(data=sampled_arr[:, :-2],
                                columns=self.ch_names,
                                index=t_array)  # left out channels STATUS and COUNTER are always present
            # print(samples.iloc[:5])
            self.o.set(
                samples,
                names=self.ch_names,
                timestamps=t_array
            )  # has to be dataframe

            # consider TMSi filewriter
            # # Initialise a file-writer class (Poly5-format) and state its file path
            # file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))


            # self.count += 1

            # if self.count > 500:
            #     print('count reached max')
            #     self.close()
        except:
            self.close()



    def close(self):
        # always run these, also in case of ctrl-c abort
        if self.use_LSL:
                # Initialise the lsl-stream
                self.stream.close()

        self.dev.stop_measurement()
        self.dev.close()

    # BACKUP CODE FOR CLOSING TMSI DEV
    # try:
    #     while True:
    #         continue
    # except KeyboardInterrupt:
    #     # This be executed when Ctrl+C is pressed
    #     pass
    # finally:
    #     # Close the file writer after GUI termination
    #     stream.close()
    #     dev.stop_measurement()
    #     # Close the connection to the SAGA device
    #     dev.close()    

    # except TMSiError as e:

    #     print("!!! TMSiError !!! : ", e.code)

    #     if (e.code == TMSiErrorCode.device_error) :

    #         print("  => device error : ", hex(dev.status.error))

    #         DeviceErrorLookupTable(hex(dev.status.error))
    #     dev.stop_measurement()
    #     dev.close()    

    # finally:

    #     # Close the connection to the device when the device is opened

    #     if dev.status.state == DeviceState.connected:
    #         dev.stop_measurement()
    #         dev.close()


if __name__ == '__main__':
    # execute
    Tmsisampler()



# Load the EEG channel set and configuration
# print("load EEG config")
# if dev.config.num_channels<64:
#     cfg = get_config("saga_config_EEG32")
# else:
#     cfg = get_config("saga_config_EEG64")
# dev.load_config(cfg)
