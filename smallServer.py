import socket
import synthesize as s
from pylab import *
ion()
import time

def recvTimeout(Sconn,timeout=.1,verbose=False):
    Sconn.setblocking(0) # make it so the socket doesn't block
    # put the data together peicewise 
    totalData=[]
    data=''
    startTime = time.time()
    while 1:
        # if you have some data then break
        if totalData and time.time()-startTime>timeout:
            break
        # if you have no data wait a little longer.
        elif time.time()-startTime > timeout*2:
            break
        # recv the data 
        try:
            data = Sconn.recv(4096)
            if data:
                totalData.append(data)
                startTime = time.time() # reset the counter
                if verbose:
                    print "recieved new packet"
            else:
                pass
        except:
            pass
    # return a string of the data
    return ''.join(totalData)

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('127.0.0.1',9000)) 
### Outside facing ip is 128.111.114.94
sock.listen(1)
print "Server is live"
while True:
    conn,addr = sock.accept()
    close('all')
    print 'Got connection from ', addr
    incoming = recvTimeout(conn,verbose=True)
    print incoming
    print "the length of the waveform recieved is ",len(incoming)
    conn.send('Thank you for connecting')
    conn.close()
    del conn

