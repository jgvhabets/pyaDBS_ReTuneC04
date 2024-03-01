from mne_bids import BIDSPath
import os
import nodes.TMSi.tmsi_utils as tmsi_utils
tmsi_utils.add_tmsi_repo()
from TMSiSDK import tmsi_device
from TMSiSDK.device import DeviceInterfaceType
from TMSiFileFormats.file_readers.xdf_reader import Xdf_Reader
from setup.saga_recorder import saga_recorder
from setup.run_timeflux import run_timeflux
from glob import glob
import mne
import json
from utils.utils import convert_time_samples
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import numpy as np
from deepmerge import always_merger
from copy import deepcopy
from pathlib import Path


class Session():

    def __init__(self, experiment_name, patient_id, medication_state, session_id):

        # make sure medication_state is either "Off" or "On"
        assert medication_state in ['Off', 'On'], f"\nmedication_state must be either 'Off' or 'On', not {medication_state}.\n"

        # set session attributes
        self.experiment_name = experiment_name
        self.patient_id = patient_id
        self.medication_state = medication_state
        self.session_id = session_id

        print(f"\nSession object initialized with the following parameters:")
        print(f"experiment_name = {experiment_name}")
        print(f"patient_id = {patient_id}")
        print(f"medication_state = {medication_state}")
        print(f"session_id = {session_id}")

        # set internal attributes
        self.calibration_run = 1

        # set directory
        self._set_directory()

        # load setup config
        self._load_setup_config()

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
        calibration_save_path = self._get_save_path("calibration", calibration_run_index)

        # check if file was already created before. If yes, query whether user wants to proceed and write file with same run index or to change run index
        if os.path.exists(calibration_save_path):
            print(f"\n{os.path.basename(calibration_save_path)} was already created before.")

            while True:
                answer = input("Do you want to overwrite the file? (y/n)")

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
        saga_recorder(calibration_save_path)

        # load data after recording finished
        calibration_save_path_tmsi = glob(str(calibration_save_path)+"*.xdf")
        reader = Xdf_Reader(filename=calibration_save_path_tmsi[0])
        calibration_data = reader.data[0]

        # Rereference the signals according to the referencing scheme in the session config
        calibration_data_reref = mne.set_bipolar_reference(
            calibration_data,
            anode=self.setup_config["reference_scheme"]["anode"],
            cathode=self.setup_config["reference_scheme"]["cathode"],
            ch_name=self.setup_config["reference_scheme"]["ch_name"],
            drop_refs=False
            )
        
        # save mne raw data
        calibration_data_reref.save(
            calibration_save_path,
            overwrite=True
            )

        # remove tmsi xdf data
        os.remove(calibration_save_path_tmsi[0])
           
    def compute_spectra(self, calibration_run_index): 
        
        # load calibration data
        self._load_calibration_data(calibration_run_index)
        
        # select rereferenced channels
        self.calibration_data.pick(self.setup_config["reference_scheme"]["ch_name"])

        # Select last 10 seconds of data. If less than 10 seconds recorded, use all data
        tmax = self.calibration_data.times[-1]
        tmin = tmax - 10
        if tmin > 0:
            self.calibration_data.crop(tmin=tmin, tmax=tmax)

        # Transform to epoch object. Epoch data to a single epoch just to enable usage tfr functions later on as these don't work on Raw objects.
        self.calibration_data_epochs = mne.make_fixed_length_epochs(
            raw=self.calibration_data,
            duration=self.calibration_data.tmax, 
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
            show=False); # plot psd       

    def finalize_configuration(self, calibration_run_index, adbs_channel, max_stim_amp):

        # get path to experiment configuration and load it if existing
        config_experiment_path = os.path.join("configs", self.experiment_name, "config_experiment.json")
        if config_experiment_path:
            with open(config_experiment_path, 'r') as file:
                    config_experiment_template = json.load(file)
        else:
            print(f"{config_experiment_path} does not exist. Provide an experiment configuration.")

        # get paths to condition configurations
        config_condition_paths = glob(os.path.join("configs", self.experiment_name, "config_condition_*.json"))

        # check whether paths exist
        if config_condition_paths:

            # if paths exist, loop over these
            for path in config_condition_paths:

                # load config
                with open(path, 'r') as file:
                    config_condition = json.load(file)

                # merge experiment and condition config, make deepcopy beforehand as merge is destructive to first argument 
                # of always_merger
                config_session = deepcopy(config_experiment_template)
                always_merger.merge(config_session, config_condition)

                # add session configuration fields
                config_session["cal"] = {"path": str(self._get_save_path("calibration", calibration_run_index))}
                config_session["rec"]["tmsi"]["aDBS_channels"] = [adbs_channel]
                config_session["stim"]["stim_amp_high"] = max_stim_amp

                # create path to session config
                config_session_save_path = self._get_save_path(config_session["condition_name"], calibration_run_index)

                # save config in session folder
                with open(config_session_save_path, 'w') as file:
                    json.dump(config_session, file, indent=2)

                # run timeflux calibration with this configuration to compute real-time power
                try:
                    run_timeflux(
                        path_graph=os.path.join("graphs", self.experiment_name, self.experiment_name + "_calibration.yml"),
                        path_config=str(config_session_save_path)
                        )
                except SystemExit as e:
                    if e.code == 0:
                        print("continuing with threshold estimation etc")
                    else:
                        raise

        else:
            print(f"No configurations matching {config_condition_paths}. Provide an condition configurations.")

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

    def _get_save_path(self, task, calibration_run_index):
       
        # set extension based on type of data to be saved
        if task == "calibration":
            extension = ".fif"
        else:
            extension = ".json"

        # update BIDSpath object of save path to account fo data specific fields
        bidspath = self.save_path.copy().update(
            task=task,
            run=calibration_run_index,
            suffix="ieeg",
            extension=extension,
            check=False
            )
        
        save_path = bidspath.fpath

        return save_path
        
    def _load_setup_config(self):
        config_filename = os.path.join("configs", self.experiment_name, "config_setup.json")
        assert os.path.exists(config_filename), f"\n{config_filename} does not exist.\n"
        with open(config_filename, 'r') as file:
            self.setup_config = json.load(file)     
    
    def _load_calibration_data(self, calibration_run_index):

        # get filename for calibration data
        calibration_save_path = self._get_save_path("calibration", calibration_run_index)

        # check if file exists with given calibration_run_index. If it exists, load it.
        if not os.path.exists(calibration_save_path):
            print("\nNo calibration file exists with this calibration_run_index. Record calibration data before loading.")
            return

        else:
            print(f"\n{calibration_save_path} will be loaded.")
            # load data to mne raw object
            self.calibration_data = mne.io.read_raw(fname=calibration_save_path)
