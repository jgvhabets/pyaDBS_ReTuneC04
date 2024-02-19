"""
Establish connection with TMSi SAGA
device, to collect data samples from.

Adjusted from https://gitlab.com/tmsi/tmsi-python-interface/

to test stand alone on WIN: python -m  nodes.TMSi.tmsi_sampler
"""

# general
import numpy as np
from pandas import DataFrame
from datetime import datetime, timezone, timedelta
import queue
from pylsl import local_clock
import nodes.TMSi.tmsi_utils as tmsi_utils
tmsi_utils.add_tmsi_repo()
import utils.utils as utils
from timeflux.core.node import Node
from TMSiSDK import tmsi_device, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, DeviceState, ChannelType
from pylsl import StreamInfo, StreamOutlet

from sys import getsizeof

class Tmsisampler(Node):
    """
    Class to connect and sample TMSi SAGA data.
    """
    def __init__(self, config_filename='config.json'):
        
        ### Load configurations
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

        ### Update TMSi configuration
        print('\t...Updating SAGA configuration...')
        # display original enabled channels and sampling rate
        print(f'Original  sampling rate: {self.dev.config.sample_rate} Hz')
        print(f'Original active channels (n={len(self.dev.channels)}):')
        
        for idx, ch in enumerate(self.dev.channels):
            print(f'channel # {idx} : "{ch.name}" in {ch.unit_name}')

        # Retrieve all channels from the device and correct accelerometer names
        self.channels = self.dev.config.channels
        self.channels = tmsi_utils.correct_ACC_channelnames(self.channels)

        # activate channels given as recording_channels in the cfg
        tmsi_utils.channel_selection(self)

        # update changes
        self.dev.config.channels = self.channels

        # set sampling rate
        self.dev.config.base_sample_rate = 4000
        sampling_rate_divider = 4000 / self.tmsi_settings['sampling_rate']
        self.dev.config.set_sample_rate(ChannelType.all_types, sampling_rate_divider)
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

        ### Setup TMSi samples extraction
                
        # create queue and link it to SAGA device
        self.queue = queue.Queue(maxsize=self.cfg['rec']['tmsi']['queue_size'])  # if maxsize=0, queue is indefinite
        sample_data_server.registerConsumer(self.dev.id, self.queue)

        # load sampling configurations
        if not self.tmsi_settings["FETCH_FULL_Q"]:
            self.MIN_TMSI_samples = self.sfreq / (1000 / self.tmsi_settings["MIN_BLOCK_SIZE_msec"])
        else:
            self.MIN_TMSI_samples = 0  # not used, but default value

        ### Setup timestamp generation and data flow method
        
        # Initialize timestamp generation method based on single wall clock time extracted on first iteration
        if self.tmsi_settings["use_wallclock_timestamp"]:
            self.first_block_taken = False
            
        # Initialize timestamp generation method based on successive additions of 1/fs. Implies using utils.output() to set timeflux output
        else:   

            # initialize output classes
            self.out_selection = utils.output(self.sfreq, self.aDBS_ch_names)
            self.out_all = utils.output(self.sfreq, self.ch_names)
      
        # Open LSL-stream via pylsl for saving of all TMSi data if save_via_lsl == True
        if self.tmsi_settings["save_via_lsl"]:
            # define number of samples of blocks to be saved in LSL
            self.n_samples_save = self.tmsi_settings["sample_secs_save_lsl"] * self.sfreq
            print(f'SET channel count buffer: {len(self.dev.channels)} plus one')
            # Initialise the lsl-stream for raw data
            # minus because of counter and status (CHECK ?)
            # plus one for later created timestamp column 
            tmsiRaw_streamInfo = StreamInfo(name="rawTMSi",
                                            type="EEG",
                                            channel_count=len(self.dev.channels) + 1,  # add extra column for timestmaps later created
                                            nominal_srate=self.sfreq,
                                            channel_format='float32')
            self.rawTMSi_outlet = StreamOutlet(
                tmsiRaw_streamInfo,
                # max_buffered=10
            )
            self.temp_raw_storing = []
            

            # Initialise the lsl-stream for raw data
            markers_streamInfo = StreamInfo(name="rawTMSi_markers",
                                            type="Markers",
                                            channel_count=1,    # length is always 1, therefore always list
                                            channel_format="string")
            self.marker_outlet = StreamOutlet(markers_streamInfo)
            # as first push, send selected channel names for saving
            self.marker_outlet.push_sample([str(self.ch_names)])  # include time

        ### Start sampling on TMSi
        self.dev.start_measurement()
        # timelag circa .4 seconds  -> starttime in first block (circa .008 - .02 sec ahead)

    def update(self):

        # Get samples from SAGA, reshape internally
        sampled_arr = self.get_samples()

        # Prepare output depending on use_wallclock_timestamp

        # If use_wallclock_timestamp == true, compute timestamps with get_stamps_for_samples(). This generates timestamps based on 
        # an initial call to datetime.now() to get the wall clock time and successive additions of 1/fs to this wall clock time for each sample 
        # fetched from TMSi. When using this method, only channels selected for aDBS will be set as timeflux output, while the full data fetched from
        # TMSi will be transmitted to LSL later.
        if self.tmsi_settings["use_wallclock_timestamp"]:
        
            # Compute timestamps for recently fetched samples
            time_array = self.get_stamps_for_samples(n_new_samples=sampled_arr.shape[0])

            # Prepare output dataframe
            samples = DataFrame(data=sampled_arr[:, :-2],  # only include data channels (i.e., not counter)
                                columns=[ch.name for ch in self.dev.channels[:-2]],
                                index=time_array)
            
            # Set timeflux output only using channels selected for aDBS
            self.o.set(
                samples.values[:, self.aDBS_channel_bool],
                names=self.aDBS_ch_names, 
                timestamps=time_array,
                meta={"rate": self.sfreq}
            )
     
        # If use_wallclock_timestamp == false, compute timestamps based on successive additions of 1/fs for each sample fetched from TMSi starting from 1/fs.
        # This is done inside out.set(). set() also adds a lsl local_clock timestamp column to the data. When using this method, different timeflux outputs 
        # will be set using either selected channels or the full dataset by employing different output names
        else:

            # Get a current lsl timestamp
            timestamp_received = local_clock()

            # Set timeflux output only using channels selected for aDBS using topic "selection"
            (self.o_selection.data,
             self.o_selection.meta)  = self.out_selection.set(
                 samples=sampled_arr[:, :-2][:,self.aDBS_channel_bool],
                 timestamp_received=timestamp_received
            )

            # Set timeflux output only using channels selected for aDBS using topic "all"     
            (self.o_all.data, 
            self.o_all.meta)  = self.out_all.set(
                samples=sampled_arr[:, :-2],
                timestamp_received=timestamp_received
            )
            

        # Transmit marker with wall clock time every iteration and regularly transmit data
        # with all channels to LSL if save_via_lsl == true and use_wallclock_timestamp == true.
        if self.tmsi_settings["use_wallclock_timestamp"] & self.tmsi_settings["save_via_lsl"]:
            
            # merge timestamps and samples to push for storing
            temp_store_arr = np.concatenate(
                [samples.values,
                 np.atleast_2d([t.timestamp() for t in time_array]).T],
                axis=1,
            )

            # send Markers every raw output: 
            # send start time and shape of block and current time
            self.marker_outlet.push_sample(
                x=[f'RAW_PUSHED (t0, shape, current_t)'
                   f'{time_array[0]},'
                   f'{samples.shape},'
                   f'{datetime.now(tz=timezone.utc)}']
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


    def get_samples(self, FETCH_UNTIL_Q_EMPTY: bool = True,
                    MIN_BLOCK_SIZE: int = 0,
                    RESHAPE_ARRAY: bool = True,):
        """
        Fetches samples from SAGA by receiving samples from
        the queue for a specified duration (MIN_BLOCK_SIZE_msec)

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

        if not self.first_block_taken:
            # get wall clock time on the first call
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
        
        return time_array

    def terminate(self):

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