""" I want to test the phase division to make sure what I implement on the AWG server behaves properly."""

from pylab import *
from matlablike import *
ion()
close('all')

freqOffset = 3e6 #Hz
freqWidth = 5e6
chirpLength = 10e-6
amplitudeScalingFactor = 1

rate = 2*freqWidth/chirpLength
timeAxis = r_[0:chirpLength:1e-9]
modulation = nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
chirp = nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
planeWave = nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
chirp*=planeWave
chirp['t',lambda x: x > chirpLength-100e-9]=1.0

phase1 = unwrap(angle(chirp.data))
phase2 = unwrap(arctan2(imag(chirp.data),real(chirp.data)))
phase3 = unwrap(arctan(imag(chirp.data),real(chirp.data)))
plot(phase1)
plot(phase2)
plot(phase3)

phase2 /= 16.
phase1 /= 16.
newWave = abs(chirp.data)*exp(1j*phase1)
newWave2 = abs(chirp.data)*exp(1j*phase1*16)
figure()
plot(chirp.data)
plot(newWave)
plot(newWave2)


show()

