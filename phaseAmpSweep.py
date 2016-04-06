""" 
im
This code puts out various amplitude and phase steps so that we can calculate something of a transfer function based on a lookup table.
"""
import labrad
import synthesize as s
from matlablike import *
import time


try:
	p
except:
	p = s.pulsegen()
close('all')

# constants
resolution = 64
amplitudeRange = linspace(0.25,.41,resolution)
phaseRange = linspace(-pi,pi,resolution)
# start at 0.27 and go to 
timeAxis = r_[0:200e-9:1e-9]
raw_input("press To start")
for phase in phaseRange:
	waveList = []
	for amplitude in amplitudeRange:
		amp = zeros([len(timeAxis)],dtype='complex')
		amp[:] = amplitude*exp(1j*phase)
		waveList.append(nddata(amp).rename('value','t').labels('t',timeAxis))
	wave = concat(waveList,'t')
	wave.labels('t',linspace(0,len(wave.data)*1e-9,len(wave.data)))
	print('running all amplitudes at phase %0.3f'%phase)
	close('all')
	ion()
	plot(wave.getaxis('t'),wave.runcopy(real).data)
	plot(wave.getaxis('t'),wave.runcopy(imag).data)
	plot(wave.getaxis('t'),wave.runcopy(abs).data)
	giveSpace()
	title('Phase Steps')
	draw()
	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)
	time.sleep(1.5)


