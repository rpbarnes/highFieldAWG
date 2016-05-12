"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

"""

import matlablike as pys
import labrad
import synthesize as s
from pylab import *
import time
try:
	p
except:
	p = s.pulsegen()

ion()

pys.close('all')
#lookupTableFile = 'LookupTable.h5/AWG_phase_amplitude_array_196.4911GHZ'
lookupTableFile = 'LookupTable.h5/ampPhaseLookup'
lookupTable = pys.nddata_hdf5(lookupTableFile)
#lookupTable = lookupTable['phase',lambda x: x > -.06]

### Input Waveform
chirpLength = 10e-6
timeAxis = pys.r_[0:chirpLength:1e-9]
freqOffset = 10e6
freqOffsetArray = pys.r_[-freqOffset:freqOffset: 1j]
freqWidth =    10e6
#freqWidth /= 16.
rate = 2*freqWidth/chirpLength
# this is the phase modulation
phaseModulation = pys.nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
# this is the frequency modulation
chirp = pys.nddata(exp(1j*phaseModulation.data)).rename('value','t').labels(['t'],[timeAxis])
ampModulation = pys.nddata(sin(pi/chirpLength*timeAxis)).rename('value','t').labels('t',timeAxis)

for countFreq,freqOffset in enumerate(freqOffsetArray):
	start = time.time()
	time.sleep(1.7)
	close('all')
	planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
	waveform = chirp*planeWave*ampModulation

	### Plot the original uncorrected pulse
	fig, ax = subplots(2,sharex=True,figsize=(14,12))
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(real).data)
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(imag).data)
	ax[0].set_title('Chirp Pulse Uncorr')

	ax[1].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
	ax[1].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
	ax[1].set_title('Chirp with Frequency Offset and Amp Modulation Uncorr')

	### Scale the lookup table to go from -1 to 1 for real and imaginary
	figure()
	pys.image(lookupTable)
	lookupTable.data /= lookupTable.data.max()
	### Calculate the correction.
	correctedData = []
	locatedData = []
	ampList =[]
	phaseList =[]
	for count,dataVal in enumerate(waveform.data):
	    currTable = lookupTable.copy() - dataVal
	    minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
	    amp = lookupTable.getaxis('amp')[minimaIndex[0]]
	    phase = lookupTable.getaxis('phase')[minimaIndex[1]]
	    correctedData.append(amp*pys.exp(1j*phase))
	    locatedData.append(lookupTable.data[minimaIndex])
	    ampList.append(amp)
	    phaseList.append(phase)
	pys.plot(array(phaseList),array(ampList),'o',markersize=5)
	pys.plot(array(phaseList),array(ampList),'--')
	locatedData = pys.nddata(array(locatedData)).rename('value','t').labels('t',waveform.getaxis('t'))
	correctedData = pys.nddata(array(correctedData)).rename('value','t').labels('t',waveform.getaxis('t'))
	smoothedData = correctedData.copy().convolve('t',5e-9)

	### Plot the original, located data and corrected pulse
	fig, ax = subplots(3,sharex=True,figsize=(14,12))
	ax[0].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
	ax[0].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
	ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(real).data)
	ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(imag).data)
	ax[0].set_title('Original Waveform and Located Waveform')


	ax[1].plot(waveform.getaxis('t'),unwrap(arctan2(waveform.runcopy(imag).data,waveform.runcopy(real).data))/16.)
	ax[1].plot(locatedData.getaxis('t'),unwrap(arctan2(locatedData.runcopy(imag).data,locatedData.runcopy(real).data))/16.)
	ax[1].plot(correctedData.getaxis('t'),unwrap(arctan2(correctedData.runcopy(imag).data,correctedData.runcopy(real).data))/16.)

	ax[2].plot(correctedData.getaxis('t'),correctedData.runcopy(real).data)
	ax[2].plot(correctedData.getaxis('t'),correctedData.runcopy(imag).data)
	ax[2].plot(smoothedData.getaxis('t'),smoothedData.runcopy(real).data)
	ax[2].plot(smoothedData.getaxis('t'),smoothedData.runcopy(imag).data)
	ax[2].set_title('Corrected Waveform')

	# synthesize the waveform
	wave = p.make_highres_waveform([('rect',0,chirpLength+1e-6)],resolution = 1e-9)
	for loop in range(len(smoothedData.data)-1):
		for constCount in range(1):
			wave.data[constCount+(loop*1)] = smoothedData.data[loop]
	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)
	print "Running Frequency %0.1f and count %i"%(freqOffset,countFreq)
	#print 'I take ',time.time() - start,' (s) to complete'
show()
