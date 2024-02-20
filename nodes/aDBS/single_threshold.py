from timeflux.core.node import Node
import pandas as pd
from pylsl import local_clock
import utils.utils as utils
from datetime import datetime, timezone


class Single_threshold(Node):

    """Implements single threshold aDBS

    Attributes:
        i (Port): Default input, expects DataFrame.
        o (Port): Default output, provides DataFrame.
    """
    def __init__(self, experiment_name=''):

        # load configuration 
        self.cfg = utils.get_config_settings(experiment_name)
        self.stim_cfg = self.cfg['stim']
        self.stim_params = pd.DataFrame(self.cfg['stim']['stim_params'], index=[0])
        self.rate = self.stim_cfg['rate']

        # set configurable attributes, convert from seconds to samples if appropriate
        # period after ramping up/down during which incoming data does not induce state changes
        self._detection_blank_period = utils.convert_time_samples(freq=self.rate, time=self.stim_cfg['detection_blank_period'])  
        # minimum period above threshold to trigger ramp up
        self._onset_period = utils.convert_time_samples(freq=self.rate, time=self.stim_cfg['onset_period'])
        # minimum period below threshold to after ramp down
        self._termination_period = utils.convert_time_samples(freq=self.rate, time=self.stim_cfg['termination_period']) 
         # period between change from low to high stim amp
        self._ramp_period = utils.convert_time_samples(freq=self.rate, time=self.stim_cfg['ramp_period'])
        # threshold that needs to be crossed for a specific onset/termination period to trigger stim ramp up/down
        self._threshold = self.stim_cfg['threshold']
        # lower stim amp
        self._stim_amp_low = self.stim_cfg['stim_amp_low'] 
        # higher stim amp
        self._stim_amp_high = self.stim_cfg['stim_amp_high'] 
        # stimulation amplitude parameter to adjust
        self._stim_amp_param = self.stim_cfg['stim_amp_param'] 

        # set housekeeping attributes
        self._loops_in_detection_blank = 0 # number of loops spent in detection blank
        self._loops_above_threshold = 0 # number of loops spent above threshold
        self._loops_below_threshold = 0 # number of loops spent below threshold
        self._loops_ramp = 0 # number of loops spent ramping

        # set state attributes
        self._stim_state = 'low'
        self._trigger_state = 'none'
        self._in_detection_blank = True
        self._stim_amp = 0
        self._stim_switch = 'off'

        # set derivative atttributes
        self._ramp_step_size = (self._stim_amp_high - self._stim_amp_low) / self._ramp_period

        # initialize output class
        self.out = utils.output(rate=self.cfg['analysis']['mean']['rate'], 
                                channels=self.stim_params.columns.tolist())


    def update(self):

        # check if stim switch had been changed via timeflux ui
        if self.i_StimSwitch.ready(): 
            
            self.check_stim_switch()

        # Make sure we have a non-empty dataframe
        if self.i_Biomarker.ready():

            # print(f'single_threshold -- data input at: {local_clock()}')

            # extract data
            data, package_id = utils.extract_data(self.i_Biomarker)

            # only proceed when stim switch is on (i.e., start signal was sent previously via timeflux ui)
            if self._stim_switch == 'on':

                # check most recent power value against threshold and set onset or termination trigger accordingly
                self.set_trigger_state(data.iloc[0,0])

                # determine next actions based on current system state
                
                # stim amp is low and onset period criterium is fulfilled -> ramp up stimulation
                if self._stim_state == 'low' and self._trigger_state == 'onset':
                    self.ramp_stim('up')
                                
                # stim amp is high and termination period criterium is fulfilled -> ramp down stimulation
                elif self._stim_state == 'high' and self._trigger_state == 'termination':
                    self.ramp_stim('down')

                # in all other conditions -> no change, just forward current stim amp and threshold
                else:
                    pass
                        
            # set current stim amp
            self.stim_params[self._stim_amp_param] = self._stim_amp

            # get current timestamp
            timestamp_received = local_clock()
            # print(f'single_threshold -- timestamp_received: {timestamp_received}')

            # Set output 
            self.o.data, self.o.meta  = self.out.set(samples=self.stim_params,
                                                     timestamp_received=timestamp_received,
                                                     package_id=package_id)
            
            # print(f'single_threshold -- sent from single_threshold at: {local_clock()}, package number {self.o.data["package_numbers"].iat[0]}, package id {self.o.data["package_ids"].iat[0]}')

    def set_trigger_state(self, value):

        # detection blank is active -> keep current system state and update detection blank
        if self._in_detection_blank == True:
            
            # update detection blank state
            self.update_detection_blank()

        # detection blank is inactive -> proceed checking value against threshold
        elif self._in_detection_blank == False:

            # value is higher than threshold -> increase above threshold loop counter
            if value > self._threshold:
                self.update_threshold_loop_counter(increase="_loops_above_threshold", 
                                                   reset="_loops_below_threshold",
                                                   period="_onset_period",
                                                   trigger_state_goal="onset",
                                                   stim_state_to_leave="low")            

            # value is lower than threshold -> increase below threshold loop counter
            elif value <= self._threshold:
                self.update_threshold_loop_counter(increase="_loops_below_threshold", 
                                                   reset="_loops_above_threshold",
                                                   period="_termination_period",
                                                   trigger_state_goal="termination",
                                                   stim_state_to_leave="high")                  

    def update_detection_blank(self):
        
        # required number of loops in detection blank have been reached -> deactivate detection blank and reset loop counter
        if self._loops_in_detection_blank == self._detection_blank_period:
            self._in_detection_blank = False
            self._loops_in_detection_blank = 0
        
        # required number of loops in detection blank have not been reached yet -> keep detection blank activated and increase loop counter
        elif self._loops_in_detection_blank < self._detection_blank_period:
            self._in_detection_blank = True 
            self._loops_in_detection_blank += 1

    def update_threshold_loop_counter(self, increase, reset, period, trigger_state_goal, stim_state_to_leave):

        # as long as period criterium not fulfilled, keep trigger state to none
        self._trigger_state == 'none'
        # increase the number of loops below/above threshold
        setattr(self, increase, getattr(self, increase) + 1)
        # reset the number of loops above/below threshold
        setattr(self, reset, 0)
        # loop counter reached period period criterium. if current stim state does not correspond to trigger state goal
        # -> set trigger state to trigger goal
        if getattr(self, increase) >= getattr(self, period) and getattr(self, "_stim_state") == stim_state_to_leave:
            self._trigger_state = trigger_state_goal
            
    def ramp_stim(self, direction):

        # set stim state goal (high or low) and ramp step (positive or negative) according to direction of ramping
        if direction == 'up':
            stim_state_goal = 'high'
            ramp_step = self._ramp_step_size
        elif direction == 'down':
            stim_state_goal = 'low'
            ramp_step = -self._ramp_step_size

        # update stimulation amplitude
        self._stim_amp += ramp_step

        # update loop counter
        self._loops_ramp += 1

        # loop counter reached ramp period -> ramping period is over, set stim state to high or low, reset counter and activate detection blank
        if self._loops_ramp == self._ramp_period:
            self._stim_state = stim_state_goal
            self._trigger_state = 'none'
            self._loops_ramp = 0
            self._in_detection_blank = True 

    def check_stim_switch(self):

        if self.i_StimSwitch.data['switch'].iat[0] == 'start':
            self._stim_switch = 'on'
            print(f'\t...aDBS activated at {datetime.now(tz=timezone.utc)}...')
        elif self.i_StimSwitch.data['switch'].iat[0] == 'stop':
            self._stim_switch = 'off'
            # reset states
            self._stim_state = 'low'
            self._trigger_state = 'none'
            self._in_detection_blank = True
            self._stim_amp = 0
            print(f'\t...aDBS deactivated at {datetime.now(tz=timezone.utc)}...')
