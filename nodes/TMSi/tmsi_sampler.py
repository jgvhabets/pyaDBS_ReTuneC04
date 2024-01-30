"""
Establish connection with TMSi SAGA
device, to collect data samples from.

Adjusted from https://gitlab.com/tmsi/tmsi-python-interface/

to test stand alone on WIN: python -m  nodes.TMSi.tmsi_sampler
"""

# %%

# general
import numpy as np
from pandas import DataFrame
from datetime import datetime, timedelta, timezone
import queue, json, time

# add tmsi repo to path
from nodes.TMSi.add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()
import nodes.TMSi.tmsi_utils as tmsi_utils
import utils.utils as utils

# tmsi repo
from timeflux.core.node import Node
from TMSiSDK import tmsi_device, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, DeviceState, ChannelType
from TMSiFileFormats.file_writer import FileWriter, FileFormat


class Tmsisampler(Node):
    """
    Class to connect and sample TMSi SAGA data.
    """
    def __init__(self):
        # load configurations
        self.cfg = utils.get_config_settings()
        self.tmsi_settings = self.cfg["rec"]["tmsi"]

        self.counter = 0

        # Initialise the TMSi-SDK first before starting using it
        print('\t...trying to initialize TMSi-SDK...')
        tmsi_device.initialize()
        print('\t...TMSi-SDK initialized...')

        print('\t...Discovering devices...')
        # Execute a device discovery. This returns a list of device-objects for every discovered device.
        discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, 
                                                DeviceInterfaceType.docked, 
                                                DeviceInterfaceType.usb)

        # Get the handle to the first discovered device.
        if (len(discoveryList) > 0):
            self.dev = discoveryList[0]
        print(f'\t...Found {discoveryList[0]}')

        # Check if connection to SAGA is not already open
        if self.dev.status.state == DeviceState.disconnected:
            # Open a connection to the SAGA
            print('\t...opening connection to SAGA...')
            self.dev.open()
            print('\t...Connection to SAGA established...')
        else:
            # Connection already open
            print('\t...Connection to SAGA already established, will not attempt to re-open...')

        print('\t...Updating SAGA configuration...')
        # display original enabled channels and sampling rate
        print(f'Original  sampling rate: {self.dev.config.sample_rate} Hz')
        print(f'Original active channels (n={len(self.dev.channels)}):')
        
        for idx, ch in enumerate(self.dev.channels):
            print(f'channel # {idx} : "{ch.name}" in {ch.unit_name}')

        # Retrieve all channels from the device and update which should be enabled
        self.channels = self.dev.config.channels
        self.channels = tmsi_utils.correct_ACC_channelnames(self.channels)

        # activate channels given as recording_channels in the cfg
        tmsi_utils.activate_channel_selection(self)

        # update changes
        self.dev.config.channels = self.channels
        # self.update_sensors()

        # set sampling rate
        self.dev.config.set_sample_rate(ChannelType.all_types, self.tmsi_settings['sampling_rate_divider'])
        self.sfreq = self.dev.config.sample_rate
        self.txdelta = timedelta(seconds=1 / self.sfreq)


        # display updated enabled channels and sampling rate
        print(f'Updated sampling rate: {self.sfreq} Hz')
        print(f'Updated active channels (n={len(self.dev.channels)}):')
        for idx, ch in enumerate(self.dev.channels):
            print(f'channel # {idx} : "{ch.name}" in {ch.unit_name}')

        for type in ChannelType:
            if (type != ChannelType.unknown) and (type != ChannelType.all_types):
                print(f'{str(type)} = {self.dev.config.get_sample_rate(type)} Hz')

        ### SETUP TMSI SAMPLES EXTRACTION
                
        # create queue and link it to SAGA device
        self.queue = queue.Queue(maxsize=self.cfg['rec']['tmsi']['queue_size'])  # if maxsize=0, queue is indefinite
        sample_data_server.registerConsumer(self.dev.id, self.queue)

        # load sampling configurations
        if not self.tmsi_settings["FETCH_FULL_Q"]:
            self.MIN_TMSI_samples = self.sfreq / (1000 / self.tmsi_settings["MIN_BLOCK_SIZE_msec"])
        else:
            self.MIN_TMSI_samples = 0  # not used, but default value

        # start sampling on tmsi
        self.dev.start_measurement()
        self.first_block_taken = False
        # timelag circa .4 seconds  -> starttime in first block (circa .008 - .02 sec ahead)
        # if self.tmsi_settings['USE_SINGLE_STARTTIME']:
        #     self.TIME_ZERO = datetime.now(tz=timezone.utc) # time at start TMSi recording

        # open direct LSL-stream
        if self.cfg['rec']['tmsi']['use_lsl']:
            # Initialise the lsl-stream
            self.stream = FileWriter(FileFormat.lsl, "SAGA")
            # Pass the device information to the LSL stream.
            self.stream.open(self.dev)

        
    def update(self):

        # try:  # comment out for debugging

            # dt = datetime.now(tz=timezone.utc) # current time
            # print(f'at start of update block: {dt}') 

        # Get samples from SAGA
        sampled_arr = self.get_samples(FETCH_UNTIL_Q_EMPTY=self.tmsi_settings["FETCH_FULL_Q"],
                                        MIN_BLOCK_SIZE=self.MIN_TMSI_samples,)
                
        # reshape samples that are given in uni-dimensional form
        sampled_arr = np.reshape(sampled_arr,
                                 (len(sampled_arr) // len(self.dev.channels),
                                 len(self.dev.channels)),
                                 order='C')
        
        # Compute timestamps for recently fetched samples
        if self.tmsi_settings['USE_SINGLE_STARTTIME']:
            if not self.first_block_taken:
                self.TIME_ZERO = datetime.now(tz=timezone.utc) # current time
                time_array = np.flip(np.array(
                    [self.TIME_ZERO - (
                        np.arange(0, sampled_arr.shape[0]) * self.txdelta
                    )]
                ).ravel())
                self.first_block_taken = True
            else:
                # create timestamp list with timedelta of sampling freq, for correct shape
                time_array = np.array(
                    [self.TIME_ZERO + (
                        np.arange(sampled_arr.shape[0]) * self.txdelta
                    )]
                ).ravel()
                # update startin time for next block, next timestamp not included in current output block
                self.TIME_ZERO += self.txdelta * sampled_arr.shape[0]

        else:
            dt = datetime.now(tz=timezone.utc) # current time
            # print(f'after getting samples: {dt}') 
            txdelta = timedelta(seconds=1 / self.dev.config.sample_rate) # time interval (i.e., 1/fs)
            time_array = np.flip(np.array([dt - (np.arange(sampled_arr.shape[0]/len(self.dev.channels)) * txdelta)]).ravel()) # create timestamp list with current timestamp as the latest timepoint
        
        dt = datetime.now(tz=timezone.utc) # current time
        print(f'CHECK TIME: end of block: {time_array[-1]}, current time: {dt}')
        samples = DataFrame(data=sampled_arr[:, :-2],
                            columns=[ch.name for ch in self.dev.channels[:-2]],
                            index=time_array) 

        # prepare timeflux output (as DataFrame)
        self.o.set(
            # rows=sampled_arr[:, :-2], # only include data channels (i.e., not counter)
            samples,
            names=[channel.name for channel in self.dev.channels[:-2]],
            timestamps=time_array,
            meta={"rate": self.sfreq})


            # consider TMSi filewriter
            # # Initialise a file-writer class (Poly5-format) and state its file path
            # file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))


            # self.count += 1

            # if self.count > 500:
            #     print('count reached max')
            #     self.close()

        # except:  # comment out for debugging
        #     self.close()


    def get_samples(self, FETCH_UNTIL_Q_EMPTY: bool = True,
                    MIN_BLOCK_SIZE: int = 0,):
        """
        Fetches samples from SAGA by receiving samples from
        the queue for a specified duration (min_sample_size_sec)

        Arguments:
            - FETCH_UNTIL_Q_EMPTY: default is true, samples
                are only pushed further when queue is empty
            - MIN_BLOCK_SIZE: only is active when FETCH_UNTIL_Q_EMPTY
                is false, if active, then window is pushed when
                this amount of samples (per variable) is present
        """
        # start with empty array
        sampled_arr = np.array([])

        # # as long as there are less samples fetched from the queue than the amount of samples available in min_sample_size_sec, continue fetching samples
        # while (len(sampled_arr) / len(self.dev.channels)) < (self.dev.config.sample_rate * self.cfg['rec']['tmsi']['min_sample_size_sec']):           
        # if there is no data available yet in the queue, wait for a bit until there is data
        # dt = datetime.now(tz=timezone.utc) # current time
        # print(f'before waiting : {dt}') 
        while self.queue.qsize() == 0:
            # print('waiting for block to fill up...')
            continue

        if FETCH_UNTIL_Q_EMPTY:
            # as long as there is data in the queue, fetch it
            while self.queue.qsize() > 0:
                # dt = datetime.now(tz=timezone.utc) # current time
                # print(f'wait complete, block there, current time: {dt}') 
                # get available samples from queue
                sampled = self.queue.get()
                # print(f'size of queue after GET: {self.queue.qsize()}')
                self.queue.task_done()  # obligatory second line to get sampled samples
                # dt = datetime.now(tz=timezone.utc) # current time
                # print(f'after getting samples: {dt}') 
                # add new samples to previously fetched samples
                sampled_arr = np.concatenate((sampled_arr, sampled.samples))
        
        else:
            # does not empty queue per se, pushes blocks when N-samples is exceeded
            while (
                len(sampled_arr) / len(self.dev.channels)
            ) < MIN_BLOCK_SIZE:
                # get available samples
                sampled = self.queue.get()
                self.queue.task_done()  # obligatory second line to get sampled samples
                # add new samples to previously fetched samples
                sampled_arr = np.concatenate((sampled_arr, sampled.samples))
                print(f'samples total length: {len(sampled_arr)}')
                
            print('number of samples fetched: '
                  f'{len(sampled_arr)/ len(self.dev.channels)}')
            print(f'size of queue after samples were fetched: {self.queue.qsize()}')

        return sampled_arr


    def close(self):

        """
        Stops recording and closes connection to SAGA device
        """

        # run close routine only if a device was found earlier
        if hasattr(self, 'dev'):

            # stop sampling if SAGA is currently sampling
            if self.dev.status.state == DeviceState.sampling:
                print('\t...Stopping recording on SAGA...')
                self.dev.stop_measurement()
                print('\t...Recording on SAGA stopped...')
            
            # close connection to SAGA if connected
            if self.dev.status.state == DeviceState.connected:
                print('\t...Closing connection to SAGA...')
                self.dev.close()
                print('\t...Connection to SAGA closed...')



if __name__ == '__main__':
    """
    run on WIN, from cd REPO: python -m nodes.TMSi.tmsi_sampler
    """
    
    # execute
    print('START MAIN CMD-EXECUTE FUNCTION')
    Tmsisampler()