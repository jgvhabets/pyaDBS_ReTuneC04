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
            print('NeurOmega is already connected, connection is now closed')
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
    print('apply TEST stimulation in init')
    
    try:
        # apply short test stim
        no_engine.AO_DefaultStimulation(
            130,  # StimFreqRight
            0.5,  # StimAmpRight_mA
            130,  # StimFreqLeft
            0.5,  # StimAmpLeft_mA
            0.5,  # Duration_Sec
        )
        print('test stim succesfully started')

        time.sleep(0.5)  # wait for 5 seconds

        _ = no_engine.AO_DefaultStopStimulation()  # return intern matlab value (no content)
        print('test stim succesfully stopped')

    except:
        print('Error caused in test stim, NO being closed...')
        _ = no_engine.AO_CloseConnection()