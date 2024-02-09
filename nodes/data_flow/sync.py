from datetime import datetime, timezone, timedelta
from timeflux.core.node import Node
import pandas as pd



class Synchronizer(Node):

    """Adds wall clock time to computed timestamps to allow for visualization via timeflux_ui

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """

    def __init__(self):

        self.first_call = True

    def update(self):
        
        # loop over input ports
        for name, suffix, port in self.iterate("i*"):
            if port.ready():
                # get timestamp if this is the first time that sync is called. add 2 seconds as ~2 seconds of data are hidden on the right in timeflux_ui
                if self.first_call:
                    self.current_time = datetime.now(tz=timezone.utc) + timedelta(seconds=2)
                    self.first_call = False
                # prepare output port
                name_out = "o" + suffix
                setattr(self, name_out, port)
                # add current time to computed timestamp
                datetime_index = pd.to_timedelta(port.data.index, unit="s") + self.current_time
                getattr(self, name_out).data.index = datetime_index
                # print(f'name {name}')
                # print(getattr(self, name_out).data)

            

