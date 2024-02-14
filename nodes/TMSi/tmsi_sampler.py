"""
Establish connection with TMSi SAGA
device, to collect data samples from.

Adjusted from https://gitlab.com/tmsi/tmsi-python-interface/

to test stand alone on WIN: python -m  nodes.TMSi.tmsi_sampler
"""

# general
import numpy as np
from pandas import DataFrame
from datetime import datetime, timedelta, timezone
import queue
from pylsl import local_clock

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

from pylsl import StreamInfo, StreamOutlet



class Tmsisampler(Node):
    """
    Class to connect and sample TMSi SAGA data.
    """
    def __init__(self, config_filename='config.json',):
        ### load configurations
        self.cfg = utils.get_config_settings(config_filename)  # use given filename in graph .yml or default config.json
           
        self.tmsi_settings = self.cfg["rec"]["tmsi"]

        ### Initialise and Connect TMSi
        print('\t...trying to initialize TMSi-SDK...')
        tmsi_device.initialize()  # init TMSi-SDK before using it
        print('\t...TMSi-SDK initialized...')

        # Execute a device discovery. This returns a list of device-objects for every discovered device.
        print('\t...Discovering devices...')
        discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, 
                                             DeviceInterfaceType.docked, 
                                             DeviceInterfaceType.usb)

        # Get the handle to the first discovered device.
        if (len(discoveryList) > 0): self.dev = discoveryList[0]
        print(f'\t...Found {discoveryList[0]}')

        # Check if connection to SAGA is not already open
        if self.dev.status.state == DeviceState.disconnected:
            print('\t...opening connection to SAGA...')
            self.dev.open()  # Open a connection to the SAGA
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
        tmsi_utils.channel_selection(self)

        # update changes
        self.dev.config.channels = self.channels
        # self.update_sensors()  # redundant in new TMSi-Python version

        # set sampling rate
        self.dev.config.base_sample_rate = 4000
        sampling_rate_divider = 4000 / self.tmsi_settings['sampling_rate']
        self.dev.config.set_sample_rate(ChannelType.all_types, sampling_rate_divider)
        self.sfreq = self.dev.config.sample_rate

        # display updated enabled channels and sampling rate
        print(f'Updated sampling rate: {self.sfreq} Hz')
        print(f'Updated active channels (n={len(self.dev.channels)}):')
        for idx, ch in enumerate(self.dev.channels):
            print(f'channel # {idx} : "{ch.name}" in {ch.unit_name}')

        for type in ChannelType:
            if (type != ChannelType.unknown) and (type != ChannelType.all_types):
                print(f'{str(type)} = {self.dev.config.get_sample_rate(type)} Hz')

        ### SETUP TMSI SAMPLES EXTRACTION ###
                
        # create queue and link it to SAGA device
        self.queue = queue.Queue(maxsize=self.cfg['rec']['tmsi']['queue_size'])  # if maxsize=0, queue is indefinite
        sample_data_server.registerConsumer(self.dev.id, self.queue)

        # load sampling configurations
        if not self.tmsi_settings["FETCH_FULL_Q"]:
            self.MIN_TMSI_samples = self.sfreq / (1000 / self.tmsi_settings["MIN_BLOCK_SIZE_msec"])
        else:
            self.MIN_TMSI_samples = 0  # not used, but default value

        # initialize output class
        self.out = utils.output(self.sfreq, self.cfg['rec']['tmsi']['recording_channels'])

        # start sampling on tmsi
        self.dev.start_measurement()
        self.first_block_taken = False
        # timelag circa .4 seconds  -> starttime in first block (circa .008 - .02 sec ahead)
        # if self.tmsi_settings['USE_SINGLE_STARTTIME']:
        #     self.TIME_ZERO = datetime.now(tz=timezone.utc) # time at start TMSi recording

        # open direct LSL-stream via tmsi packages
        if self.tmsi_settings['use_lsl']:
            # Initialise the lsl-stream
            self.stream = FileWriter(FileFormat.lsl, "SAGA")
            # Pass the device information to the LSL stream.
            self.stream.open(self.dev)


        # open LSL-stream via pylsl for saving of all TMSi
        if self.tmsi_settings['save_via_lsl']:
            # Initialise the lsl-stream for raw data
            tmsiRaw_streamInfo = StreamInfo(name="rawTMSi",
                                            type="EEG",
                                            channel_count=len(self.channels) + 1,
                                            nominal_srate=self.sfreq,)
            self.rawTMSi_outlet = StreamOutlet(tmsiRaw_streamInfo)
            self.temp_raw_storing = []
            # define number of samples of blocks to be saved in LSL
            self.n_samples_save = self.tmsi_settings["sample_secs_save_lsl"] * self.sfreq

            # Initialise the lsl-stream for raw data
            markers_streamInfo = StreamInfo(name="rawTMSi_markers",
                                            type="Markers",
                                            channel_count=1,    # length is always 1, therefore always list
                                            channel_format="string")
            self.marker_outlet = StreamOutlet(markers_streamInfo)
            # as first push, send selected channel names for saving
            self.marker_outlet.push_sample(self.ch_names)  # include time

        
        
    def update(self):

        timestamp_received = local_clock()
        # prepare timeflux output (as DataFrame)
        self.o.data, self.o.meta  = self.out.set(samples=sampled_arr[:, :-3],
                                                 timestamp_received=timestamp_received)
        # comment out for debugging
        # try:

        # Get samples from SAGA, reshape internally
        sampled_arr = self.get_samples()
        
        # Compute timestamps for recently fetched samples
        time_array = self.get_stamps_for_samples(n_new_samples=sampled_arr.shape[0])

        ### SETTING TIMEFLUX OUTPUT (as DataFrame)

        # prepare output dataframe
        samples = DataFrame(data=sampled_arr[:, :-2],  # only include data channels (i.e., not counter)
                            columns=[ch.name for ch in self.dev.channels[:-2]],
                            index=time_array)
        
        if self.cfg["LSL_workflow"]:
            # set all active channels as timeflux output 
            self.o.set(
                samples,
                names=[channel.name for channel in self.dev.channels[:-2]],
                timestamps=time_array,
                meta={"rate": self.sfreq}
            )
        
        else:
            # only set channels selected for aDBS as timeflux output
            self.o.set(
                samples.values[:, self.aDBS_channel_bool],
                names=self.aDBS_ch_names,
                timestamps=time_array,
                meta={"rate": self.sfreq}
            )

        ### SAVING OF RAW DATA

        # merge timestamps and samples to push for storing
        if self.tmsi_settings["save_via_lsl"]:
            temp_store_arr = np.concatenate(
                [samples.values, time_array], axis=1,
            )

            # send Markers every raw output: 
            # send start time and shape of block and current time
            self.marker_outlet.push_sample(
                x=['RAW_PUSHED (t0, shape, current_t)',
                   time_array[0],
                   samples.shape,
                   datetime.now(tz=timezone.utc)]
            )

            # send sampled array plus used timestamps (in array)
            # for saving LSL clock is used
            
            # add to existing or new storing block
            if len(self.temp_raw_storing) > 0:
                self.temp_raw_storing = np.concatenate(
                    [self.temp_raw_storing, temp_store_arr],
                    axis=0
                )
            else:  # create new storing block
                self.temp_raw_storing = temp_store_arr

            # send if present stored block is long enough
            if self.temp_raw_storing.shape[0] > self.n_samples_save:
                self.rawTMSi_outlet.push_chunk(
                    x=self.temp_raw_storing,
                    pushthrough=True,
                )
                self.temp_raw_storing = []  # clean up
            


        
        # consider TMSi filewriter
        # # Initialise a file-writer class (Poly5-format) and state its file path
        # file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))


            

        # except:  # comment out for debugging
        #     self.close()


    def get_samples(self, FETCH_UNTIL_Q_EMPTY: bool = True,
                    MIN_BLOCK_SIZE: int = 0,
                    RESHAPE_ARRAY: bool = True,):
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
        FETCH_UNTIL_Q_EMPTY=self.tmsi_settings["FETCH_FULL_Q"]
        MIN_BLOCK_SIZE=self.MIN_TMSI_samples

        # start with empty array
        sampled_arr = np.array([])

        # if there is no data available yet in the queue, wait for a bit until there is data
        while self.queue.qsize() == 0:
            continue

        if FETCH_UNTIL_Q_EMPTY:
            # as long as there is data in the queue, fetch it
            while self.queue.qsize() > 0:
                # get available samples from queue
                sampled = self.queue.get()
                self.queue.task_done()  # obligatory second line to get sampled samples
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

        # reshape samples that are given in uni-dimensional form
        if RESHAPE_ARRAY:
            sampled_arr = np.reshape(sampled_arr,
                                     (len(sampled_arr) // len(self.dev.channels),
                                     len(self.dev.channels)),
                                     order='C',)

        return sampled_arr


    def get_stamps_for_samples(self, n_new_samples):
        """
        Arguments:
            - n_new_samples: numer of rows of new sampled
                array
        
        Returns:
            - array containing timestamps based on last
                timestamp where previous block stopped
        """
        if self.tmsi_settings['USE_SINGLE_STARTTIME']:
            if not self.first_block_taken:
                self.TIME_ZERO = datetime.now(tz=timezone.utc) # current time
                time_array = np.flip(np.array(
                    [self.TIME_ZERO - (
                        np.arange(0, n_new_samples) * self.txdelta
                    )]
                ).ravel())
                self.first_block_taken = True
            else:
                # create timestamp list with timedelta of sampling freq, for correct shape
                time_array = np.array(
                    [self.TIME_ZERO + (
                        np.arange(n_new_samples) * self.txdelta
                    )]
                ).ravel()
                # update startin time for next block, next timestamp not included in current output block
                self.TIME_ZERO += self.txdelta * n_new_samples

        else:
            dt = datetime.now(tz=timezone.utc) # current time
            # print(f'after getting samples: {dt}') 
            txdelta = timedelta(seconds=1 / self.dev.config.sample_rate) # time interval (i.e., 1/fs)
            # create timestamp list with current timestamp as the latest timepoint
            time_array = np.flip(np.array(
                [dt - (np.arange(n_new_samples/len(self.dev.channels)) * txdelta)]
            ).ravel())
        
        return time_array


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