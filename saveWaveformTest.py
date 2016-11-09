"""
write something to save the waveform that specman sends to the server.
"""
import time
from pylab import *
import numpy as np
from astropy.table import Table,Column
from astropy.io import ascii
ion()

timeArray = arange(1,1000)*1e-9
wave = exp(1j*2*pi*10e6*timeArray)

figure()
plot(timeArray,wave)
show()


fileName = 'savedWaveforms/'+str(time.strftime("%Y-%m-%d_%H-%M"))+'.dat'
dataWriter = Table([real(wave),imag(wave)],names=['real','imag'])
ascii.write(dataWriter,fileName)



