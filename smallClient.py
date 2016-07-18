import socket
import numpy as np

def stringify(inputArray):
    string = ''
    for val in inputArray:
        string += ' '+str(round(val,6))
    return string


x = np.linspace(0,10,30000)
x = stringify(x)
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serverAddress = ('127.0.0.1',9000) # address to the xepr computer
#serverAddress = ('localhost',7000) # address to the xepr computer
sock.connect(serverAddress)
print "sending %i data values"%len(x)
sock.send(x)
print sock.recv(128)
sock.close()

