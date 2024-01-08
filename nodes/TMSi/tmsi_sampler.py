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

# tmsi repo
from timeflux.core.node import Node
from TMSiSDK import tmsi_device, sample_data_server
from TMSiSDK.device import DeviceInterfaceType, DeviceState, ChannelType
from TMSiFileFormats.file_writer import FileWriter, FileFormat

# load configuration 
with open('config.json', 'r') as file:
    cfg = json.load(file)

class Tmsisampler(Node):
    """
    Class to connect and sample TMSi SAGA data.
    """
    def __init__(self):

        self.cfg = cfg
        self.counter = 0

        try:
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
                print('[{0}] : [{1}] in [{2}]'.format(idx, ch.name, ch.unit_name))

            # activate channels given as recording_channels in the cfg
            self.ch_names = self.dev.config.channels 
            for channel in self.ch_names:
                if channel.name in self.cfg['rec']['tmsi']['recording_channels']:
                    channel.enabled = True
                else:
                    channel.enabled = False
            self.dev.config.channels = self.ch_names

            # set sampling rate
            self.dev.config.set_sample_rate(ChannelType.all_types, self.cfg['rec']['tmsi']['sampling_rate_divider'])

            # display updated enabled channels and sampling rate
            print(f'Updated sampling rate: {self.dev.config.sample_rate} Hz')
            print(f'Updated active channels (n={len(self.dev.channels)}):')
            for idx, ch in enumerate(self.dev.channels):
                print('[{0}] : [{1}] in [{2}]'.format(idx, ch.name, ch.unit_name))

            for type in ChannelType:
                if (type != ChannelType.unknown) and (type != ChannelType.all_types):
                    print('{0} = {1} Hz'.format(str(type), self.dev.config.get_sample_rate(type)))

            # create queue and link it to SAGA device
            self.queue = queue.Queue(maxsize=self.cfg['rec']['tmsi']['queue_size'])  # if maxsize=0, queue is indefinite
            sample_data_server.registerConsumer(self.dev.id, self.queue)

            # start sampling on tmsi
            self.dev.start_measurement()

            if self.cfg['rec']['tmsi']['use_lsl']:
                # Initialise the lsl-stream
                self.stream = FileWriter(FileFormat.lsl, "SAGA")
                # Pass the device information to the LSL stream.
                self.stream.open(self.dev)

        except:
            print('\t...__init__ within TMSiSampler failed...')
            self.close()  # closes both dev.measurement and dev itself

    def update(self):

        try:

            dt = datetime.now(tz=timezone.utc) # current time
            print(f'at start of update block: {dt}') 

            # Get samples from SAGA
            sampled_arr = np.array([])
            sampled_arr = self.get_samples(sampled_arr)

            # dt = datetime.now(tz=timezone.utc) # current time
            # print(f'after getting samples: {dt}') 

            # Compute timestamps for recently fetched samples
            txdelta = timedelta(seconds=1 / self.dev.config.sample_rate) # time interval (i.e., 1/fs)
            t_array = np.flip(np.array([dt - (np.arange(sampled_arr.shape[0]/len(self.dev.channels)) * txdelta)]).ravel()) # create timestamp list with current timestamp as the latest timepoint
            print(f'beginning time array: {t_array[:5]}')
            print(f'end of time array: {t_array[-5:]}')

            dt = datetime.now(tz=timezone.utc) # current time
            print(f'after creating timestamps: {dt}') 

            # reshape samples that are given in uni-dimensional form
            sampled_arr = np.reshape(sampled_arr,
                                     (len(sampled_arr) // len(self.dev.channels),
                                      len(self.dev.channels)),
                                      order='C')
            
            # dt = datetime.now(tz=timezone.utc) # current time
            # print(f'after reshaping: {dt}')          
            
            # samples = DataFrame(data    = sampled_arr[:, :-2],
            #                     columns = [channel.name for channel in self.dev.channels[:-2]],
            #                     index   = t_array) 
            # print(samples)

            # prepare timeflux output
            self.o.set(
                rows=sampled_arr[:, :-2], # only include data channels (i.e., not counter)
                names=[channel.name for channel in self.dev.channels[:-2]],
                timestamps=t_array)

            # print(samples)

            # has to be dataframe

            # consider TMSi filewriter
            # # Initialise a file-writer class (Poly5-format) and state its file path
            # file_writer = FileWriter(FileFormat.poly5, join(measurements_dir,"Example_envelope_plot.poly5"))


            # self.count += 1

            # if self.count > 500:
            #     print('count reached max')
            #     self.close()
        except:
            self.close()

    def get_samples(self, sampled_arr):

        """
        Fetches samples from SAGA by receiving samples from the queue for a specified duration (min_sample_size_sec)
        """

        # # as long as there are less samples fetched from the queue than the amount of samples available in min_sample_size_sec, continue fetching samples
        # while (len(sampled_arr) / len(self.dev.channels)) < (self.dev.config.sample_rate * self.cfg['rec']['tmsi']['min_sample_size_sec']):           
        # if there is no data available yet in the queue, wait for a bit until there is data
        # dt = datetime.now(tz=timezone.utc) # current time
        # print(f'before waiting : {dt}') 
        while self.queue.qsize() == 0:
            # print('waiting for block to fill up...')
            continue

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

            # print(f'number of samples fetched: {len(sampled_arr)/3}')
            # print(f'size of queue after samples were fetched: {self.queue.qsize()}')

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
    # execute
    print('START MAIN CMD-EXECUTE FUNCTION')
    Tmsisampler()