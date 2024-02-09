import json
import pandas as pd
import numpy as np


def get_config_settings(
    json_filename: str = 'config.json',
):
    # load configuration 
    with open(json_filename, 'r') as file:
        cfg = json.load(file)

    return cfg

def convert_time_samples(freq, time=None, samples=None):

    # compute time if number of samples is given
    if samples is not None:
        time = int(samples / freq)
        return time
    # compute samples if time is given
    elif time is not None:
        samples = int(time * freq)
        return samples

def extract_data(port):
    
    # drop timestamp and package columns
    package_id = np.unique(port.data["package_ids"])
    data = port.data.drop(columns=["timestamps_received", "package_numbers", "package_ids"])

    return data, package_id

class output:

    def __init__(self, rate, channels):

        self.package_number = 1
        self.rate = rate
        self.txdelta = 1 / rate
        self.base_timestamp = self.txdelta
        self.channels = channels + ["timestamps_received", "package_numbers", "package_ids"]
        self.meta = {"rate":self.rate}

    def set(self, samples, timestamp_received, package_id=None):
      
        # get number of rows in data
        nrows = samples.shape[0]

        # compute timestamps by adding txdelta onto base_timestamp for each row in data
        timestamps_computed = np.array(
                    [self.base_timestamp + (
                        (np.arange(nrows)) * self.txdelta
                    )]
                    ).ravel()
        
        # expand package number and timestamp_received to match the number of rows in data
        timestamps_received = np.full((nrows, 1), timestamp_received)
        package_numbers = np.full((nrows, 1), self.package_number)

        # Set package_id. package_id can be used to identify packages of samples and their derivatives across nodes.
        # If no package_id provided, use set package_id as package_number. 
        if package_id is not None:
            package_ids = np.full((nrows, 1), package_id)
        else:
            package_ids = package_numbers

        # concatenate samples with timestamps_received, package_number and package_id
        rows = np.hstack((samples, timestamps_received, package_numbers, package_ids))

        # set data as dataframe as required by timeflux Port object
        data = pd.DataFrame(rows, index=timestamps_computed, columns=self.channels)
        
        # increment base_timestamp and package_number
        self.base_timestamp += self.txdelta * data.shape[0]
        self.package_number +=1

        return data, self.meta
        
