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
freqWidthArray = arange(0,2.5,.5)*1e6 # frequency at 200 Ghz
chirpLength = 1e-6
tau = .5e-6
amplitudeScalingFactor = 1
wave = p.make_highres_waveform([('rect',0,2*chirpLength+tau+1e-6)],resolution = 1e-9)
wave.data *= amplitudeScalingFactor
timeAxis = r_[0:chirpLength:1e-9]


# make wave and scale amplitude of rectangular pulse
for freqWidth in freqWidthArray:
	freqWidth /= 16.
	raw_input('Press Enter to run freqWidth %0.1f'%(freqWidth))
	close('all')
	rate = 2*freqWidth/chirpLength
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

	toSynth = wave.copy()
	toSynth['t',0:len(chirpP.data)] = chirpP.data
	toSynth['t',(len(chirpP.data)+int(tau/1e-9)):(len(chirpP.data)+int(tau/1e-9)+len(chirpM.data))] = chirpM.data
	ax[1].plot(toSynth.getaxis('t'),toSynth.runcopy(real).data)
	ax[1].plot(toSynth.getaxis('t'),toSynth.runcopy(imag).data)
	ax[1].set_title('Chirp with Frequency Offset')
	draw()
	#


	sram = p.wave2sram(toSynth.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)

