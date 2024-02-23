from mne_bids import BIDSPath
import os
import nodes.TMSi.tmsi_utils as tmsi_utils
tmsi_utils.add_tmsi_repo()
from TMSiSDK import tmsi_device
from TMSiSDK.device import DeviceInterfaceType
from TMSiFileFormats.file_readers.xdf_reader import Xdf_Reader
from setup.saga_recorder import saga_recorder
from glob import glob
import mne
import json
from utils.utils import convert_time_samples
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import numpy as np


class Session():

    def __init__(self, experiment_name, patient_id, medication_state, session_id):

        # make sure medication_state is either "Off" or "On"
        assert medication_state in ['Off', 'On'], f"\nmedication_state must be either 'Off' or 'On', not {medication_state}.\n"

        # set session attributes
        self.experiment_name = experiment_name
        self.patient_id = patient_id
        self.medication_state = medication_state
        self.session_id = session_id

        print(f"\nSession object initialized with params:")
        print(f"experiment_name = {experiment_name}")
        print(f"patient_id = {patient_id}")
        print(f"medication_state = {medication_state}")
        print(f"session_id = {session_id}")

        # set internal attributes
        self.calibration_run = 1

        # set directory
        self._set_directory()

    def set_saga_configuration(self):

        # Get directory of saga config and make sure config exists
        config_filename = os.path.join("configs", self.experiment_name, "config_saga.xml")
        assert os.path.exists(config_filename), f"\n{config_filename} does not exist.\n"

        # Execute a device discovery. This returns a list of device-objects for every discovered device.
        print('\t...Discovering devices...')
        discoveryList = tmsi_device.discover(tmsi_device.DeviceType.saga, 
                                             DeviceInterfaceType.docked, 
                                             DeviceInterfaceType.usb)

        # Get the handle to the first discovered device.
        if (len(discoveryList) > 0): 
            self.dev = discoveryList[0]
            print(f'\t...Found {discoveryList[0]}')

        # Open a connection to the SAGA-system
        print('\t...opening connection to SAGA...')
        self.dev.open()
        print('\t...Connection to SAGA established...')

        try:

            # Print current device configuation
            print('\nCurrent device configuration:')
            self._print_device_config()

            # Load configuration
            print('\n\t...updating configuration...')
            self.dev.load_config(config_filename)
            print('\t...Configuration updated...')

            # Print updated device configuation
            print('\nUpdated device configuration:')
            self._print_device_config()

        finally:

            # Close connection to the SAGA-system
            print('\n\t...closing connection to SAGA...')
            self.dev.close()
            print('\t...Connection to SAGA closed...')

    def record_calibration_data(self, calibration_run_index):

        # get filename for calibration data
        self._get_calibration_save_path(calibration_run_index)

        # check if file was already created before. If yes, query whether user wants to proceed and write file with same run index or to change run index
        if glob(os.path.join(
            self.calibration_save_path.directory,
            self.calibration_save_path.basename + "*.xdf" # account for TMSi adding date and time to the filename
            )):
            print(f"\n{self.calibration_save_path.basename} was already created before.")

            while True:
                answer = input("Do you want to record to a file with the same calibration_run_index? (y/n)")

                if answer in ("y", "n"):

                    if answer == "n":
                        print("Recording aborted. Please change calibration_run_index.")
                        return

                    if answer == "y":
                        print("Recording will be started.")
                        break

                else:
                    print("Invalid answer. Provide either y (yes) or n (no)")

        else:
            print("\nRecording will be started.")            

        # record calibration data
        saga_recorder(self.calibration_save_path)

    def load_calibration_data(self, calibration_run_index):

        # get filename for calibration data
        self._get_calibration_save_path(calibration_run_index)

        # get files matching calibration save path accounting for timestamps added to filename by TMSi
        calibration_save_path_all = glob(os.path.join(
            self.calibration_save_path.directory,
            self.calibration_save_path.basename + "*.xdf" # account for TMSi adding date and time to the filename
            ))

        # check if more than one file exists with given calibration_run_index. If yes, query which file to load.
        if len(calibration_save_path_all) == 0:
            print("\nNo calibration file exists with this calibration_run_index. Record calibration data before loading.")

        if len(calibration_save_path_all) == 1:
            self.calibration_save_path = calibration_save_path_all[0]
            print(f"\n{self.calibration_save_path} will be loaded.")

        elif len(calibration_save_path_all) > 1:
            print("\nMore than one calibration file exists with this calibration_run_index:")
            for idx, path in enumerate(calibration_save_path_all):
                print(f"File index: {idx}: {path}")

            while True:
                file_idx = int(input("Which file do you want to load? (file index)"))

                try:
                    self.calibration_save_path = calibration_save_path_all[file_idx]
                    print(f"\n{self.calibration_save_path} will be loaded.")
                    break

                except:
                    print("File index provided is incorrect. Provide the integer following File index.")

        # load data to mne raw object
        reader = Xdf_Reader(filename=self.calibration_save_path)
        self.calibration_data = reader.data[0]

    def compute_spectra(self):
     
        # Load directory of session config
        config_filename = os.path.join("configs", self.experiment_name, "config_session.json")
        assert os.path.exists(config_filename), f"\n{config_filename} does not exist.\n"
        with open(config_filename, 'r') as file:
            session_config = json.load(file)

        # Rereference the signals according to the referencing scheme in the session config
        self.calibration_data_reref = mne.set_bipolar_reference(
            self.calibration_data,
            anode=session_config["reference_scheme"]["anode"],
            cathode=session_config["reference_scheme"]["cathode"])
        self.calibration_data_reref.drop_channels(self.calibration_data.info.ch_names, on_missing='ignore')
        
        # Select last 10 seconds of data. If less than 10 seconds recorded, use all data
        tmax = self.calibration_data_reref.times[-1]
        tmin = tmax - 10
        if tmin > 0:
            self.calibration_data_reref.crop(tmin=tmin, tmax=tmax)

        # Transform to epoch object. Epoch data to a single epoch just to enable usage tfr functions later on as these don't work on Raw objects.
        self.calibration_data_epochs = mne.make_fixed_length_epochs(
            raw=self.calibration_data_reref,
            duration=self.calibration_data_reref.tmax, 
            overlap=0)

        # Compute welch psd
        window = convert_time_samples(freq=self.calibration_data_epochs.info['sfreq'], time=1)
        self.calibration_data_psd = self.calibration_data_epochs.compute_psd(
            method="welch",
            picks="all",
            fmin=2, 
            fmax=100, 
            n_fft=window, 
            n_per_seg=window, 
            n_overlap=window/2
            )
        
        # compute morlet wavelet transformation
        self.calibration_data_tfr = mne.time_frequency.tfr_morlet(
            self.calibration_data_epochs,
            freqs=np.arange(1,100.5,0.5),
            n_cycles=4,
            picks="all",
            return_itc=False
            )

        # set ploting options
        plt.style.use('default') # use default matplotlib style to ensure correct viz when using dark mode
        cmap = get_cmap("Set1") # get colormap

        # plot psd
        fig = self.calibration_data_psd.plot(
            picks="all", 
            amplitude=True, 
            dB=False, 
            spatial_colors=False,
            show=False)
        for color, line in zip(cmap.colors, fig.axes[0].lines):
            line.set_color(color) # change color of each line
            line.set_linewidth(1)
        fig.axes[0].set_title("PSD")

        # plot TFR
        self.calibration_data_tfr.plot(
            picks="all",
            cmap=("viridis", True), 
            dB=False, 
            title="auto",
            vmin = 0,
            vmax = np.percentile(self.calibration_data_tfr.data, 98),
            show=False) # plot psd       

    def _set_directory(self):

            # create BIDS root directory with sourcedata and rawdata subfolder
            root_dir = os.path.join("C:\\", "Measurements", self.experiment_name)
            if not os.path.exists(root_dir):
                os.makedirs(os.path.join(root_dir, "sourcedata"))
                os.makedirs(os.path.join(root_dir, "rawdata"))

            # create a BIDSpath object using the session infos provided
            self.save_path = BIDSPath(
                root=os.path.join(root_dir, "sourcedata"),
                datatype="ieeg",
                subject=self.patient_id, 
                session="EphysMed"+self.medication_state+f"{self.session_id:02d}"
                )

            # check whether this directory already exists. If no, create it, if yes, use this one but raise a warning.
            if os.path.exists(self.save_path.directory):
                print(f"\n{self.save_path.directory} was already created before."
                    "\nThis directory will now be used to save data, but consider setting a different session_id if you want to set up a new session.\n")

            else:
                self.save_path.mkdir()
                print(f"\n{self.save_path.directory} created successfully.\n")

    def _print_device_config(self):

        print('Base-sample-rate: \t\t{0} Hz'.format(self.dev.config.base_sample_rate))
        print('Sample-rate: \t\t\t{0} Hz'.format(self.dev.config.sample_rate))
        print('Interface-bandwidth: \t\t{0} MHz'.format(self.dev.config.interface_bandwidth))
        print('Reference Method: \t\t', self.dev.config.reference_method)
        print('Sync out configuration: \t', self.dev.config.get_sync_out_config())
        print('Triggers:\t\t\t', self.dev.config.triggers )
        print('Channels:')
        for idx, ch in enumerate(self.dev.channels):
            print('[{0}] : [{1}] in [{2}]'.format(idx, ch.name, ch.unit_name))

    def _get_calibration_save_path(self, calibration_run_index):
        
        self.calibration_save_path = self.save_path.copy().update(
            task="calibration",
            run=calibration_run_index,
            extension=".xdf",
            check=False
            )