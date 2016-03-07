""" 
This is a model of what specman should send to the server program


Variable parameters:
    IP address
    Port number
    wavefromString

"""

import socket


wavefromString = 'WAVEFORM, DELAY 10, RECT 20 0, DELAY 20, RECT 40 0, DELAY 10000, OFFSET 0.01 0.07, IMBALANCE 0.8 1.0\n' # All time units are given in ns. The phase for the RECT pulse is in rad.

# the two terms offset and imbalance can come at any time of the wavefrom sequece as they only provide constants to modify the entire waveform sequence by.

# client end
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '127.0.0.1' # we would like this to be user set, so that it can write to a server on the local host or one in the LAN.
port = 12345
s.connect((host,port))
s.send(wavefromString) # note it is necessary to send a new line character '\n' to signify the end of the waveform string.

ready = s.recv(1024)
print ready
s.close()
    






