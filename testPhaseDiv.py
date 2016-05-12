""" I want to test the phase division to make sure what I implement on the AWG server behaves properly."""

from pylab import *
from matlablike import *
ion()
close('all')

freqOffset = 1e6 #Hz
freqWidth = 25e6
chirpLength = 10e-6
amplitudeScalingFactor = 1

rate = 2*freqWidth/chirpLength
timeAxis = r_[0:chirpLength:1e-9]
modulation = nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
chirp = nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])

phase1 = unwrap(angle(chirp.data))
phase2 = unwrap(arctan2(real(chirp.data),imag(chirp.data)))
plot(phase1)
plot(phase2)

phase2 /= 16.
newWave = abs(chirp.data)*exp(1j*phase2)
figure()
plot(chirp.data)
plot(newWave)


show()

