"""
Establish connection with Newronika alphaDBS
device, to collect data samples from.
Copied from https://github.com/jlbusch/C04
"""


import numpy as np
from pandas import DataFrame
import serial
from timeflux.core.node import Node

class interface(Node):

    def __init__(self) -> None:
        
        # init variables
        self.Int2Store = 0
        self.cnt = 0
        self.FillBuffer = 0
        self.cnt_Time = 0
        self.ReceivedBuffer = np.zeros(21, dtype='i') 
        self.sample_ch1 = [] # variable to store serial reading and plotting for online mode
        self.sample_ch2 = [] # variable2 to store serial reading and plotting for online mode
        self.Order = []

        # set portname (updated based on Labor PC on Nov 28, 2022)
        self.portname = 'COM5'

        # init serial object
        self.NWK_SerialCon = serial.Serial(
            self.portname,
            baudrate=38400,
            bytesize = 8,
            parity = serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout = 1
        )
    

    # timeflux output function
    def update(self):
        # update output port
        ch1, ch2 = sampleFromDevice(self)

        if type(ch1) != list and type(ch1) != np.array:
            ch1 = list(ch1)
            ch2 = list(ch2)
        
        self.o.set(
            DataFrame(
                data=np.array([ch1, ch2]).T,
                columns=['nwk_ch1', 'nwk_ch2']
            )
        )
        print(f'NEWRONIKA SAMPLER OUT: {self.o.data}')


def sampleFromDevice(self):   

    self.sample_ch1 = []
    self.sample_ch2 = []
    self.Sum = 0
    self.CheckSum = 0
    
    while not self.sample_ch1:

        # loop until values appear on serial port
        while self.NWK_SerialCon.inWaiting() == 0: 
                pass
            
        # read serial port   
        self.NWKString = self.NWK_SerialCon.read(size=1)  
        self.Int2Store = ord(self.NWKString)
                
        if self.FillBuffer == 1:
            self.ReceivedBuffer[self.cnt] = self.Int2Store
            self.cnt += 1
            
        if self.Int2Store == 5 and self.cnt == 0:
            self.ReceivedBuffer[self.cnt] = self.Int2Store
            self.cnt += 1
            
        if self.Int2Store == 200 and self.cnt == 1:
            self.ReceivedBuffer[self.cnt] = self.Int2Store
            self.cnt += 1
            
        if self.Int2Store == 1 and self.cnt == 2:
            self.ReceivedBuffer[self.cnt] = self.Int2Store
            self.cnt += 1
            self.FillBuffer = 1
                
        if self.cnt == 21:
            self.cnt = 0
            self.FillBuffer = 0
            Sum = 0
            CheckSum = 0
            while(self.cnt < 16):
                Sum += int(self.ReceivedBuffer[self.cnt])
                self.cnt += 1    
            self.cnt = 0
            
            
            CheckSum = (int(self.ReceivedBuffer[16]) << 8) + int(self.ReceivedBuffer[17])
            
            if (Sum == CheckSum and Sum != 0):
                self.sample_ch1.append((((int(self.ReceivedBuffer[4])<<8) + int(self.ReceivedBuffer[5]))*2)/4096) # Save first value of sample1 on array 
                self.sample_ch2.append((((int(self.ReceivedBuffer[6])<<8) + int(self.ReceivedBuffer[7]))*2)/4096) # Save first value of sample2 on array 
                self.Order.append(int(self.ReceivedBuffer[8]))
                
                self.cnt_Time = self.cnt_Time + 1
                
                self.sample_ch1.append((((int(self.ReceivedBuffer[10])<<8) + int(self.ReceivedBuffer[11]))*2)/4096) # Save second value of sample1 on array 
                self.sample_ch2.append((((int(self.ReceivedBuffer[12])<<8) + int(self.ReceivedBuffer[13]))*2)/4096) # Save second value of sample2 on array
                self.Order.append(int(self.ReceivedBuffer[14]))
                            
                self.cnt_Time = self.cnt_Time + 1

            else:
                pass
            self.cnt = 0

    # create tuple of both sampled channels
    return self.sample_ch1, self.sample_ch2


def closeConnectionToDevice(self):

        self.NWK_SerialCon.flushInput()
        self.NWK_SerialCon.close()
