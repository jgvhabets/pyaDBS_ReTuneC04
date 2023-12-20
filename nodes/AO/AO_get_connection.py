"""
establish connection with AlphaOmega's
NeuroOmega
"""
import time
import neuroomega_matlab as no


def connect_AO(AO_connection: str = 'MATLAB',
               AO_MAC: str = "F4:5E:AB:6B:6D:A1"):
    
    assert AO_connection.upper() in ['MATLAB', 'C'], 'invalid AO_connection'
    
    print(f'...connecting AO via {AO_connection}')
    if AO_connection.upper() == 'MATLAB':
        # use AO matlab wrapper
        no_engine = no.get_engine()

        if no_engine.AO_IsConnected():
            no_engine.AO_CloseConnection()
        
        no_engine.AO_DefaultStartConnection(AO_MAC)
        
        for n in range(10):  # give 10 seconds for AO connection
            time.sleep(1)
            
            if no_engine.AO_IsConnected():  # no.isConnected():
                print("Connection to NeuroOmega established.")
                
                return no_engine    
        
        if not no_engine.AO_IsConnected():  # no.isConnected():
            raise ValueError(
                "Connection to NeuroOmega could not be established."
                "Ending program. Please check the connection and try again."
            )
    

    elif AO_connection.upper() == 'C':

        print('to make')
        raise ValueError('not existing AO-C++ connector')


def apply_and_stop_test_stim(no_engine):

    try:
        # apply short test stim
        no_engine.AO_DefaultStimulation(
            StimFreqRight=130,
            StimAmpRight_mA=0.5,
            StimFreqLeft=23,
            StimAmpLeft_mA=0.5,
            Duration_Sec=10.0,
        )
        print('test stim succesfully started')

        for i in range(5): time.sleep(5)  # wait for 5 seconds

        no_engine.AO_DefaultStopStimulation()
        print('test stim succesfully started')

    except:
        print('Error caused in test stim, NO being closed...')
        closed = no_engine.AO_CloseConnection()