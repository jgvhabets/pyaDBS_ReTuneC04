'''
(c) 2022 Twente Medical Systems International B.V., Oldenzaal The Netherlands

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#######  #     #   #####   #
   #     ##   ##  #        
   #     # # # #  #        #
   #     #  #  #   #####   #
   #     #     #        #  #
   #     #     #        #  #
   #     #     #  #####    #


Establish LSL-connection from TMSi SAGA
device, to collect data samples from.

Extracted from https://gitlab.com/tmsi/tmsi-python-interface/

'''
# general
import json

# add tmsi repo to path
from nodes.TMSi.add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()

# tmsi repo
from TMSiSDK import tmsi_device
from TMSiSDK.error import DeviceErrorLookupTable, TMSiError, TMSiErrorCode
from TMSiSDK.device import DeviceInterfaceType, DeviceState, ChannelType
from TMSiFileFormats.file_writer import FileWriter, FileFormat

# load configuration 
with open('config.json', 'r') as file:
    cfg = json.load(file)

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
        dev = discoveryList[0]
    print(f'\t...Found {discoveryList[0]}')

    # Check if connection to SAGA is not already open
    if dev.status.state == DeviceState.disconnected:
        # Open a connection to the SAGA
        print('\t...opening connection to SAGA...')
        dev.open()
        print('\t...Connection to SAGA established...')
    else:
        # Connection already open
        print('\t...Connection to SAGA already established, will not attempt to re-open...')

    print('\t...Updating SAGA configuration...')
    # display original enabled channels and sampling rate
    print(f'Original  sampling rate: {dev.config.sample_rate} Hz')
    print(f'Original active channels (n={len(dev.channels)}):')
    for idx, ch in enumerate(dev.channels):
        print('[{0}] : [{1}] in [{2}]'.format(idx, ch.name, ch.unit_name))

    # activate channels given as recording_channels in the cfg
    ch_names = dev.config.channels 
    for channel in ch_names:
        if channel.name in cfg['rec']['tmsi']['recording_channels']:
            channel.enabled = True
        else:
            channel.enabled = False
    dev.config.channels = ch_names

    # set sampling rate
    dev.config.set_sample_rate(ChannelType.all_types, cfg['rec']['tmsi']['sampling_rate_divider'])

    # display updated enabled channels and sampling rate
    print(f'Updated sampling rate: {dev.config.sample_rate} Hz')
    print(f'Updated active channels (n={len(dev.channels)}):')
    for idx, ch in enumerate(dev.channels):
        print('[{0}] : [{1}] in [{2}]'.format(idx, ch.name, ch.unit_name))

    for type in ChannelType:
        if (type != ChannelType.unknown) and (type != ChannelType.all_types):
            print('{0} = {1} Hz'.format(str(type), dev.config.get_sample_rate(type)))

    # Initialise the lsl-stream
    stream = FileWriter(FileFormat.lsl, "SAGA")

    # Pass the device information to the LSL stream.
    stream.open(dev)

    # start sampling on tmsi
    dev.start_measurement()
    
except TMSiError as e:
    print("!!! TMSiError !!! : ", e.code)
    if (e.code == TMSiErrorCode.device_error) :
        print("  => device error : ", hex(dev.status.error))
        DeviceErrorLookupTable(hex(dev.status.error))
        close()
        
def close():

# Stops recording and closes connection to SAGA device

    # run close routine only if a device was found earlier
    if dev:

        # stop sampling if SAGA is currently sampling
        if dev.status.state == DeviceState.sampling:
            print('\t...Stopping recording on SAGA...')
            dev.stop_measurement()
            print('\t...Recording on SAGA stopped...')
        
        # close LSL stream if opened
        stream.close(dev)

        # close connection to SAGA if connected
        if dev.status.state == DeviceState.connected:
            print('\t...Closing connection to SAGA...')
            dev.close()
            print('\t...Connection to SAGA closed...')

        