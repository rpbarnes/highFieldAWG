""" 
This code puts out various amplitude and phase steps so that we can calculate something of a transfer function based on a lookup table.
"""
import labrad
import synthesize as s
from matlablike import *
import time

import socket
from pylab import *
ion()

try:
	p
except:
	p = s.pulsegen()
close('all')

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('128.111.114.94',9000)) # this will work if coming from computer but I think this will need to be changed to the outside address for functionality with the specman comp.
#sock.bind(('127.0.0.1',9000)) 
### Outside facing ip is 128.111.114.94

sock.listen(5)
print "Server is live"


# constants
resolution = 64
phaseResolution = 10
amplitudeRange = linspace(0.01,.11,resolution)
amplitudeRange = linspace(0.60,.95,resolution)
phaseRange = linspace(-pi,pi,phaseResolution)
# start at 0.27 and go to 
timeAxis = r_[0:200e-9:1e-9]
count = 0
while True:
    conn,addr = sock.accept()
    temp = conn.recv(16384000) 
    phase = phaseRange[count]
    close('all')
    start = time.time()
    waveList = []
    for amplitude in amplitudeRange:
        amp = zeros([len(timeAxis)],dtype='complex')
        amp[:] = amplitude*exp(1j*phase)
        waveList.append(nddata(amp).rename('value','t').labels('t',timeAxis))
    wave = concat(waveList,'t')
    wave.labels('t',linspace(0,len(wave.data)*1e-9,len(wave.data)))
    print "recieved interrupt running next"
    print "step %i / %i"%(count +1,len(phaseRange))
    sram = p.wave2sram(wave.data)
    sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
    p.fpga.dac_run_sram_slave(sram,False)
    count += 1
    conn.send('Thank you for connecting')
    conn.close()
    if count >= len(phaseRange):
        break


