""" 
This code makes a chirp pulse defined by the frequency width and the center frequency relative to the carrier as well as the length of the pulse.

The chirp plays at the beginning of the pulse followed by 1's

"""
import labrad
import synthesize as s
from matlablike import *

try:
	p
except:
	p = s.pulsegen()
close('all')

# constants
freqOffset = 00e6 #Hz
freqWidthArray = arange(3.1,5.1,.1)*1e6
chirpLengthArray = arange(.5,10.5,.5)*1e-6 # seconds
rate = 2*(3.6/16)*1e6/1e-6
amplitudeScalingFactor = 1

# make wave and scale amplitude of rectangular pulse
for chirpLength in chirpLengthArray:
	raw_input('Press Enter to run %0.3f'%freqWidth)
	close('all')
	wave = p.make_highres_waveform([('rect',0,chirpLength+1e-6)],resolution = 1e-9)
	wave.data *= amplitudeScalingFactor
	timeAxis = r_[0:chirpLength:1e-9]
	#freqWidth /= 16.
	#rate = 2*freqWidth/chirpLength
	freqWidth = rate*chirpLength/2
	# this is the phase modulation
	modulation = nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
	# this is the frequency modulation
	chirp = nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
	planeWave = nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
	# plot the chirp before frequency offset
	ion()
	fig, ax = subplots(2,sharex=True)
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(real).data)
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(imag).data)
	ax[0].set_title('Chirp Pulse')

	chirp*=planeWave
	wave['t',0:len(chirp.data)] = chirp.data
	ax[1].plot(wave.getaxis('t'),wave.runcopy(real).data)
	ax[1].plot(wave.getaxis('t'),wave.runcopy(imag).data)
	ax[1].set_title('Chirp with Frequency Offset')
	draw()
	#


	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)

