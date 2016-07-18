""" 
This is a model of what specman should send to the server program


Variable parameters:
    IP address
    Port number
    wavefromString

"""

import socket
from pylab import *
from matlablike import *

def stringify(inputArray):
    string = ''
    for val in inputArray:
        string += str(round(val,6)) + ',' 
    return string

def makeWaveform(incomingString):
    """ Produce a waveform with modifiers from incoming string recieved by server"""
    real = incomingString.split('real:')[1].split('imag:')[0].split(',')
    real.pop(-1)
    real = array([float(k) for k in real])
    imag = incomingString.split('imag:')[1].split(',')
    imag.pop(-1)
    imag = array([float(k) for k in imag])
    return real + 1j*imag 

x = linspace(0,10,15000)
### Stuff for chirp pulse
freqOffset = 1e6 #Hz
freqWidth = 25e6
chirpLength = 10e-6
amplitudeScalingFactor = 1
rate = 2*freqWidth/chirpLength
timeAxis = r_[0:chirpLength:1e-9]
modulation = nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
chirp = nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
re = stringify(real(chirp.data))
im = stringify(imag(chirp.data))


wavefromString = 'real: '+re + 'imag: ' + im +'\\n'

# the two terms offset and imbalance can come at any time of the wavefrom sequece as they only provide constants to modify the entire waveform sequence by.

# client end
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1' # we would like this to be user set, so that it can write to a server on the local host or one in the LAN.
port = 9000
s.connect((host,port))
s.send(wavefromString) # note it is necessary to send a new line character '\n' to signify the end of the waveform string.

ready = s.recv(1024)
print ready
s.close()
    






