"""
Perform DBS via AlphaOmega NeurOmega

to test run alone (WIN): python -m nodes.AO.AO_stim

chronic stim source: https://github.com/jlbusch/C04/blob/dev/stim_AO/stim_AO.m
"""

# import public packages
import cython
from pandas import DataFrame
# from dataclasses import dataclass
from timeflux.core.node import Node



class AO_stim(Node):
    """
    
    Raises:
        - ValueError if incorrect input_signal is given
    
    """
    def __init__(
        self,
        # stimChannel,
        # timeRun,
        # stimAmpLow,
        # nLoopsIdle,
        # minEstimatesRampDown,
        # minEstimatesRampUp,
        # threshold,
        # nLoopsUpdateThreshold,
        # nLoopsDetectionBlank,
        # nLoopsRamp,
        cfg_file_path = None
    ):

        # load cfg
        cfg = cfg_file_path 

        self.stimChannel = cfg.device.no.stimChannel
        self.timeRun = cfg.run.timeRun
        self.stimAmpLow = cfg.stim.ampLow
        self.nLoopsIdle = cfg.stim.nLoopsIdle
        self.minEstimatesRampDown = cfg.stim.minEstimatesRampDown
        self.minEstimatesRampUp = cfg.stim.minEstimatesRampUp
        self.threshold = cfg.stim.thresholdAbs
        self.nLoopsUpdateThreshold = cfg.stim.nLoopsUpdateThreshold
        self.nLoopsDetectionBlank = cfg.stim.nLoopsDetectionBlank
        self.nLoopsRamp = cfg.stim.nLoopsRamp

        
        # % Compute stimulation amplitude step during ramp up/down
        # obj.stimStep = (cfg.stim.ampHigh - cfg.stim.ampLow)/cfg.stim.nLoopsRamp;
        
        # Necessary?? Extract fieldtrip real time buffer header
        # obj.hdr = cfg.help.ftrt.hdr

        # connect to AO
        ## TODO: find function on Labor PC; 'C:\CODE\Neuro Omega System SDK' 
        macNO = 'F4:5E:AB:6B:6D:A1'
        AO_DefaultStartConnection(macNO)
        assert AO_IsConnected() == 1, (
            'Connection to NeuroOmega failed'
        )
        print('Connection to NeuroOmega established! :)') 


        ### SET STARTING STATES
        # % init states
        self.stimHigh = False
        self.stimLow = False
        self.rampUp = False
        self.rampDown = False
        
        # % init loops and steps
        self.idleLoop = 1
        self.updateLoop = 1
        self.step = 0
        self.idleFlag = True
        
        # % init nEstimatesUnderThreshold & nEstimatesOverThreshold 
        self.nEstimatesUnderThr = 0
        self.nEstimatesOverThr = 0
        
        # % init threshold state & stimamp
        self.thresholdState = 0
        # self.stimAmp = obj.stimAmpLow

    def update(self):

        # TODO: check source: https://github.com/jlbusch/C04/blob/dev/aDBS_newronika/stim/stimulator.m
        # either use buffer before, or wait here to gather enough samples
        # activate NO with stimStandard_NO()  (Labor PC?)

        input_value =  self.i.data.values[0, 0]
        # print('input value:', input_value, int(input_value > self._threshold))
        output = int(input_value > self._threshold)
        # print('EXC THRESH', output)

        # sets as pandas DataFrame
        self.o.data = DataFrame(
            data=[[input_value, output]],
            columns=['IN (biomarker)',
                     'OUT (aDBS trigger)'],
            index=self.i.data.index
        )
        # print(self.o.data)