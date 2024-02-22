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

/**
 * @file ${example_EEG_workflow.py} 
 * @brief This example shows the functionality of the impedance plotter and the 
 * data stream plotter. The example is structured as if an EEG measurement is
 * performed, so the impedance plotter is displayed in head layout. The channel 
 * names are set to the name convention of the TMSi EEG cap using a 
 * pre-configured EEG configuration. Measurement data is saved to poly5 or 
 * xdf-file, depending on user input.
 *
 */


'''
import nodes.TMSi.tmsi_utils as tmsi_utils
tmsi_utils.add_tmsi_repo()
import sys
from os.path import join

from PySide2 import QtWidgets

from TMSiSDK import tmsi_device
from TMSiPlotters.gui import PlottingGUI
from TMSiPlotters.plotters import PlotterFormat
from TMSiSDK.device import DeviceInterfaceType, DeviceState
from TMSiFileFormats.file_writer import FileWriter, FileFormat
from TMSiSDK.error import TMSiError, TMSiErrorCode, DeviceErrorLookupTable

def saga_recorder(save_path):

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
            
            # Check if there is already a plotter application in existence
            plotter_app = QtWidgets.QApplication.instance()
            
            # Initialise the plotter application if there is no other plotter application
            if not plotter_app:
                plotter_app = QtWidgets.QApplication(sys.argv)
                        
            
            # Initialise the desired file-writer class and state its file path
            file_writer = FileWriter(FileFormat.xdf, join(save_path))
            
            # Define the handle to the device
            file_writer.open(dev)
        
            # Define the GUI object and show it 
            # The channel selection argument states which channels need to be displayed initially by the GUI
            plot_window = PlottingGUI(plotter_format = PlotterFormat.signal_viewer,
                                    figurename = 'A RealTimePlot', 
                                    device = dev)
            plot_window.show()
            
            # Enter the event loop
            plotter_app.exec_()
            
            # Quit and delete the Plotter application
            QtWidgets.QApplication.quit()
            del plotter_app
            
            # Close the file writer after GUI termination
            file_writer.close()
            
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