"""
A server to grant basic operation of the DAC board from specman.

Basic operation: Specman sends a string (that describes a waveform) to the server, the server decides how to compose the waveform and sends this to the DAC board.

Specman should send a string to the server. The string parameterizes a predefined waveform that the server will send the DAC board.  

The string will define the waveform such as: Terms described below. 
'WAVEFORM, DELAY td1, ADIABATIC tp1 vp1, DELAY td2, RECTX tp2 vp2, DELAY td3, OFFSET dcI dcQ, IMBALANCE I Q'

The WAVEFORM term tells the server that the following string pertains to playing a waveform.

Terms DELAY, ADIABATIC, and RECTX tell the server what pulse to play. These are predefined in the server. Specman should be able to take an input from the user for the string that it is to send. 

Variables tdx, tpx, and vpx parameterize the given pulses, these should be parameterized by the user on the specman end.

Commas separate out given pulse types e.g. 'DELAY' 'RECTX' etc.

Terms OFFSET and IMBALANCE tell the server how to modify the data sequence sent to the DAC. OFFSET describes the DC offset for the I and Q channels defined by dcI and dcQ and IMBALANCE describes the proportional factor to multiply the I and Q channel data by. Both of these terms need to be user modifyable in specman.

Currently the DAC board will play a waveform indefinitely. Specman should send the waveform string and wait for a reply from the server that says 'the dac is running', meaning the waveform that was just sent is now playing. Right now the server sends a '1' back to the client, once the waveform is synthesized.
	

"""
import threading
import socket
import pylab as pl
import numpy as np


### Various Functions#{{{
def makeWaveform(waveformList):#{{{
    """ Take the string sent from specman and compose a waveform. """
    currentWaveform = np.zeros(0,dtype='complex128')
    for command in waveformList:
        command = command.split(' ')
        command = filter(None,command)
        thisPart = None
        if 'WAVEFORM' in command[0]:
            pass
        elif 'DELAY' in command[0]:
            # structure should be 'DELAY d1' where d1 is the length of delay in ns
            thisPart = np.zeros(int(command[1]))
            currentWaveform = np.concatenate((currentWaveform,thisPart))
        elif 'RECT' in command[0]:
            thisPart = np.ones(int(command[1]))*np.exp(1j*float(command[2]))
            currentWaveform = np.concatenate((currentWaveform,thisPart))
        elif 'OFFSET' in command[0]:
            dcI,dcQ = float(command[1]),float(command[2])
        elif 'IMBALANCE' in command[0]: 
            I,Q = float(command[1]),float(command[2])
        else:
            print "I do not understand what '%s' means..."%command[0]
            pass
    realW,imagW = np.real(currentWaveform),np.imag(currentWaveform)
    ### multiply the imbalance and subtract the offset
    realW*=I
    realW-=dcI
    imagW*=Q
    imagW-=dcQ
    
    modifiedWaveform = realW + 1j*imagW
    return modifiedWaveform
#}}}

def synthesize(waveToSynthesize):#{{{
    """ For demonstration purposes this just plots the waveform. """
    timeAxis = np.arange(0,len(waveToSynthesize),1)*1e-9 
    pl.figure()
    pl.plot(timeAxis,np.real(waveToSynthesize))
    pl.plot(timeAxis,np.imag(waveToSynthesize))
    pl.show()
    # once the waveform is synthesized this releases and sends a 'ready' back to the client.
#}}}
#}}}


#{{{ # Server
host = 'localhost'
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, 12345)) 
s.listen(10)
while True:
    print 'Ready for command'
    conn, addr = s.accept()
    print 'created connection at ' , addr
    incoming = ''
    command_buffer = []
    while True:
        temp = conn.recv(1024) 

        if not temp: break
        incoming = incoming + temp
        if incoming[-1] != '\n':
            if incoming.find('\n'):
                temp = incoming.split('\n')
                command_buffer.extend(temp[:-1])
                incoming = temp[-1]
            else:
                break
        else:
            command_buffer.extend(incoming.split('\n'))
            incoming = ''
        print "about to try to run the command buffer:",repr(command_buffer)
        for mycommand in command_buffer:
            if len(mycommand) == 0:
                pass
            else:
                mycommand = mycommand.split(',')
                if mycommand[0] == 'WAVEFORM': #decipher string and synthesize waveform
                    waveform = makeWaveform(mycommand)
                    synthesize(waveform)
                    conn.send('1')
                else:
                    pass

    conn.close()
        

#}}}
