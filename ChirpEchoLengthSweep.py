""" 
This is looking for a chirp'd echo. 

Chirp(+) - tau - Chirp(-) - tau - Echo

This makes two chirp pulses and sweeps the length of the pulses. 

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
freqWidth = 1e6
chirpLengthArray = arange(3,10.5,.5)*1e-6 # seconds
tau = 1e-6
amplitudeScalingFactor = 1


freqWidth /= 16.
# make wave and scale amplitude of rectangular pulse
for chirpLength in chirpLengthArray:
	raw_input('Press Enter to run pulse length %0.1f'%(chirpLength*1e-6))
	close('all')
	wave = p.make_highres_waveform([('rect',0,2*chirpLength+tau+1e-6)],resolution = 1e-9)
	wave.data *= amplitudeScalingFactor
	timeAxis = r_[0:chirpLength:1e-9]
	rate = 2*freqWidth/chirpLength
	print rate
	# this is the phase modulation
	modulation = nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
	# this is the frequency modulation
	chirpP = nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
	chirpM = nddata(exp(1j*(-1)*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
	# plot the chirp before frequency offset
	ion()
	fig, ax = subplots(2,sharex=True)
	ax[0].plot(chirpP.getaxis('t'),chirpP.runcopy(real).data)
	ax[0].plot(chirpP.getaxis('t'),chirpP.runcopy(imag).data)
	ax[0].plot(chirpM.getaxis('t'),chirpM.runcopy(real).data)
	ax[0].plot(chirpM.getaxis('t'),chirpM.runcopy(imag).data)
	ax[0].set_title('Chirp Pulse')

	wave['t',0:len(chirpP.data)] = chirpP.data
	wave['t',(len(chirpP.data)+int(tau/1e-9)):(len(chirpP.data)+int(tau/1e-9)+len(chirpM.data))] = chirpM.data
	ax[1].plot(wave.getaxis('t'),wave.runcopy(real).data)
	ax[1].plot(wave.getaxis('t'),wave.runcopy(imag).data)
	ax[1].set_title('Chirp with Frequency Offset')
	draw()
	#


	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)

