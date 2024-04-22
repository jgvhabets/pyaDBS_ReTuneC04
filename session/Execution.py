import os
from mne_bids import BIDSPath
from session.run_timeflux import run_timeflux

class Execution():

    def __init__(self, experiment_name, patient_id, medication_state, session_id, calibration_id):

        # make sure medication_state is either "Off" or "On"
        assert medication_state in ['Off', 'On'], f"\nmedication_state must be either 'Off' or 'On', not {medication_state}.\n"

        # set session attributes
        self.experiment_name = experiment_name
        self.patient_id = patient_id
        self.medication_state = medication_state
        self.session_id = session_id
        self.calibration_id = calibration_id

        print(f"Execution object initialized with the following parameters:\n")
        print(f"experiment_name = {experiment_name}")
        print(f"patient_id = {patient_id}")
        print(f"medication_state = {medication_state}")
        print(f"session_id = {session_id}")
        print(f"calibration_id = {calibration_id}")

        # check whether directory exists
        self._check_save_path()

    def start_stimulation(self, condition_name):

            # get path to session configuration for this condition 
            config_session_path = self._get_session_path(condition_name)
            assert os.path.exists(config_session_path), f"\n{config_session_path} does not exist. Provide a session configuration.\n"

            # run timeflux
            try:
                run_timeflux(
                    path_graph=os.path.join("graphs", self.experiment_name, self.experiment_name + ".yml"),
                    path_config=str(config_session_path)
                    )
                
            # close without error message
            except SystemExit as e:
                if e.code == 0:              
                    print("Stimulation terminated.")
                else:
                    raise

    def _check_save_path(self):
       
        # set BIDS root directory
        root_dir = os.path.join("C:\\", "LFP_recordings", "Measurements", self.experiment_name)

        # create a BIDSpath object using the session infos provided
        self.save_path = BIDSPath(
            root=os.path.join(root_dir, "sourcedata"),
            datatype="ieeg",
            subject=self.patient_id, 
            session="EphysMed"+self.medication_state+f"{self.session_id:02d}"
            )

        # check whether this directory exists
        assert os.path.exists(self.save_path.directory), f"\n{self.save_path.directory} does not exist. Set up session before executing the experiment.\n"

    def _get_session_path(self, condition_name):
       
        # update BIDSpath object of save path to account fo data specific fields
        bidspath = self.save_path.copy().update(
            task=condition_name,
            run=self.calibration_id,
            suffix="ieeg",
            extension=".json",
            check=False
            )
        
        session_path = bidspath.fpath

        return session_path