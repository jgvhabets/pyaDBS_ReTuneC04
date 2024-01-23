"""Example program to demonstrate how to send a multi-channel time series to
LSL."""

from timeflux.core.node import Node
import random
from pylsl import StreamInfo, StreamOutlet, local_clock
import pandas as pd

class DummyLslStream(Node):

    def __init__(self):

        # first create a new stream info (here we set the name to BioSemi,
        # the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
        # last value would be the serial number of the device or some other more or
        # less locally unique identifier for the stream as far as available (you
        # could also omit it but interrupted connections wouldn't auto-recover).
        info = StreamInfo('dummy', 'EEG', 1, 100, 'float32', 'myuid34234')
        chns = info.desc().append_child("channels")
        chn = chns.append_child("channel")
        chn.append_child_value("label", 'dummy_channel')

        # next make an outlet
        self.outlet = StreamOutlet(info)

        print('Starting dummy stream')

    def update(self):
        # make a new random 8-channel sample; this is converted into a
        # pylsl.vectorf (the data type that is expected by push_sample)
        mysample = [random.random()]
        # now send it and wait for a bit
        self.outlet.push_sample(mysample)
        # dummy output
