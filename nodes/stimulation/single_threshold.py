import json, mne
from timeflux.core.node import Node
import pandas as pd
from pylsl import local_clock
import nodes.AO as ao


class Single_threshold(Node):

    """Implements single threshold aDBS

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """
    def __init__(self):

        # load configuration 
        with open('config.json', 'r') as file:
            cfg = json.load(file)

        # init stimulator class
        self.stimulator = ao.AO_stim_matlab

        # set configurable attributes 
        self._detection_blank_period = cfg['stim']['detection_blank_period'] # period after ramping up/down during which incoming data does not induce state changes
        self._onset_period = cfg['stim']['onset_period'] # minimum period above threshold to trigger ramp up
        self._termination_period = cfg['stim']['termination_period'] # minimum period below threshold to after ramp down
        self._ramp_period = cfg['stim']['ramp_period'] # period to change between low and high stim amp
        self._threshold = cfg['stim']['threshold'] # threshold that needs to be crossed for a specific onset/termination period to trigger stim ramp up/down

        # set housekeeping attributes
        self._loops_in_detection_blank = 0 # number of loops spent in detection blank
        self._loops_above_threshold = 0 # number of loops spent above threshold
        self._loops_below_threshold = 0 # number of loops spent below threshold
        self._loops_ramp = 0 # number of loops spent ramping

        # set state attributes
        self._stim_state = 'low'
        self._threshold_state == 'none'
        

    def update(self):
        
        # Make sure we have a non-empty dataframe
        if self.i.ready():
            
            # detection blank is active -> keep current system state and update detection blank
            if self._in_detection_blank == True:
                
                # update detection blank state
                self.update_detection_blank()
            
            # detection blank is inactive -> proceed
            elif self._in_detection_blank == False:

                # check most recent power value against threshold and return whether onset or termination period criterium is fulfilled
                self._threshold_state = self.check_against_threshold(self.i.data.value)

                # determine next actions based on current system state
                
                # stim amp is low and onset period criterium is fulfilled -> ramp up stimulation
                if self._stim_state == 'low' and self._threshold_state == 'onset':
                    self.ramp_stim('up')
                                
                # stim amp is high and termination period criterium is fulfilled -> ramp down stimulation
                elif self._stim_state == 'high' and self._threshold_state == 'termination':
                    self.ramp_stim('down')
                              
                # stim amp is ramping up -> keep ramping up until upper stim amp is reached
                elif self._stim_state == 'ramp_up':
                    self.ramp_stim('up')
                
                # stim amp is ramping down -> keep ramping down until lower stim amp is reached
                elif self._stim_state == 'ramp_down':
                    self.ramp_stim('down')

                # in all other conditions -> just proceed current stim amp and threshold
                else:
                    pass
                
            # update stimulation parameters on stimulation device
            self.stimulator.update()
            
            # set current stim amp and threshold state as output to send it to lsl stream
            
            

    def update_detection_blank(self):
        
        # required number of loops in detection blank have been reached -> deactivate detection blank and reset loop counter
        if self._loops_in_detection_blank == self._detection_blank_period:
            self._in_detection_blank = False
            self._loops_in_detection_blank = 0
        
        # required number of loops in detection blank have not been reached yet -> keep detection blank activated and increase loop counter
        elif self._loops_in_detection_blank < self._detection_blank_period:
            self._in_detection_blank = True 
            self._loops_in_detection_blank += 1

    def check_against_threshold(self, value):

        # value is higher than threshold -> increase above threshold loop counter
        if value > self._threshold:
            self._loops_above_threshold += 1
            self._loops_below_threshold = 0
            # loop counter reached onset period -> set threshold state to onset
            if self._loops_above_threshold == self._onset_period:
                self._threshold_state == 'onset'            

        # value is lower than threshold -> increase below threshold loop counter
        elif value <= self._threshold:
            self._loops_below_threshold += 1
            self._loops_above_threshold = 0
            # loop counter reached termination period -> set threshold state to termination
            if self._loops_below_threshold == self._termination_period:
                self._threshold_state == 'termination'

        else:
            self._threshold_state == 'none'

    def ramp_stim(self, direction):

        # set stim state goal (high or low) and ramp step (positive or negative) according to direction of ramping
        if direction == 'up':
            stim_state_goal = 'high'
            ramp_step = self._ramp_step_size
        elif direction == 'down':
            stim_state_goal = 'low'
            ramp_step = -self._ramp_step_size

        # update stimulation amplitude
        self.stimulator.stim_amp += ramp_step

        # update loop counter
        self._loops_ramp += 1

        # loop counter reached ramp period -> ramping period is over, set stim state to high or low and reset counter
        if self._loops_ramp == self._ramp_period:
            self._stim_state = stim_state_goal
            self._loops_ramp = 0
