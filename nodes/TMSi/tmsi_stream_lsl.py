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
# import general packages
import numpy as np
from pandas import DataFrame
import queue

# import timeflux node
from timeflux.core.node import Node
# import tmsi SDK
from nodes.TMSi.add_tmsi_repo import add_tmsi_repo
add_tmsi_repo()
from TMSiSDK import tmsi_device
from TMSiSDK.device import DeviceInterfaceType, ChannelType
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable


try:
    # Initialise the TMSi-SDK first before starting using it
    tmsi_device.initialize()
    
    # Execute a device discovery. This returns a list of device-objects for every discovered device.
    discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, DeviceInterfaceType.docked, 
                                         DeviceInterfaceType.usb)

    if (len(discoveryList) > 0):
        # Get the handle to the first discovered device.
        dev = discoveryList[0]
        
        # Open a connection to the SAGA-system
        dev.open()


        ch_list = dev.config.channels

        for i_ch, ch in enumerate(ch_list):

                if ch.type == ChannelType.AUX and ch.name in ['X', 'Y', 'Z']:
                    ch.enabled = True
                    print(f'channel {i_ch} ENABLED ({ch.name})')
                
                else:
                    ch.enabled = False

        dev.config.channels = ch_list
        dev.update_sensors()

        dev.start_measurement()

        
        # Initialise the lsl-stream
        stream = FileWriter(FileFormat.lsl, "SAGA")
        
        # Pass the device information to the LSL stream.
        stream.open(dev)

        # while True:
        #     continue
    
        # Close the file writer after GUI termination
        stream.close()
        
        # Close the connection to the SAGA device
        dev.close()
    
except TMSiError as e:
    print("!!! TMSiError !!! : ", e.code)
    if (e.code == TMSiErrorCode.device_error) :
        print("  => device error : ", hex(dev.status.error))
        DeviceErrorLookupTable(hex(dev.status.error))
        
finally:
    # Close the connection to the device when the device is opened
    if dev.status.state == DeviceState.connected:
        dev.close()