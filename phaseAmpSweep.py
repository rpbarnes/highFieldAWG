""" 
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
phaseResolution = 512
amplitudeRange = linspace(0.01,.11,resolution)
amplitudeRange = linspace(0.60,.95,resolution)
phaseRange = linspace(-pi,pi,phaseResolution)
# start at 0.27 and go to 
timeAxis = r_[0:200e-9:1e-9]
raw_input("press To start")
for count,phase in enumerate(phaseRange):
	start = time.time()
	waveList = []
	for amplitude in amplitudeRange:
		amp = zeros([len(timeAxis)],dtype='complex')
		amp[:] = amplitude*exp(1j*phase)
		waveList.append(nddata(amp).rename('value','t').labels('t',timeAxis))
	wave = concat(waveList,'t')
	wave.labels('t',linspace(0,len(wave.data)*1e-9,len(wave.data)))
	print('running all amplitudes at phase %0.3f'%phase)
	print "step",count +1
	#close('all')
	#ion()
	#plot(wave.getaxis('t'),wave.runcopy(real).data)
	#plot(wave.getaxis('t'),wave.runcopy(imag).data)
	#plot(wave.getaxis('t'),wave.runcopy(abs).data)
	#giveSpace()
	#title('Phase Steps')
	#draw()
	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)
	#answer=raw_input("press for next")
	#if answer=='kill':
	#	break
	time.sleep(3.5)
	print "cycle time is: ",time.time()-start


