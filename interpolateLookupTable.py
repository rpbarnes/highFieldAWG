"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

"""

import matlablike as pys

close('all')
lookupTableFile = 'LookupTable.h5/ampPhaseLookup'
lookupTable = pys.nddata_hdf5(lookupTableFile)

### Input Waveform
chirpLength = 1e-6
timeAxis = r_[0:chirpLength:1e-9]
freqOffset = 0e6
freqWidth = 10e6
freqWidth /= 16.
rate = 2*freqWidth/chirpLength
# this is the phase modulation
phaseModulation = pys.nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
# this is the frequency modulation
chirp = pys.nddata(exp(1j*phaseModulation.data)).rename('value','t').labels(['t'],[timeAxis])
planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
ampModulation = pys.nddata(sin(pi/chirpLength*timeAxis)).rename('value','t').labels('t',timeAxis)
waveform = chirp*planeWave*ampModulation

### Plot the original uncorrected pulse
fig, ax = subplots(2,sharex=True)
ax[0].plot(chirp.getaxis('t'),chirp.runcopy(real).data)
ax[0].plot(chirp.getaxis('t'),chirp.runcopy(imag).data)
ax[0].set_title('Chirp Pulse Uncorr')

ax[1].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
ax[1].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
ax[1].set_title('Chirp with Frequency Offset and Amp Modulation Uncorr')

### Scale the lookup table to go from -1 to 1 for real and imaginary
lookupTable.data /= lookupTable.data.max()
### Calculate the correction.
correctedData = []
locatedData = []
for count,dataVal in enumerate(waveform.data):
    currTable = lookupTable.copy() - dataVal
    minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
    amp = lookupTable.getaxis('amp')[minimaIndex[0]]
    phase = lookupTable.getaxis('phase')[minimaIndex[1]]
    correctedData.append(amp*pys.exp(1j*phase))
    locatedData.append(lookupTable.data[minimaIndex])
locatedData = pys.nddata(array(locatedData)).rename('value','t').labels('t',waveform.getaxis('t'))
correctedData = pys.nddata(array(correctedData)).rename('value','t').labels('t',waveform.getaxis('t'))

### Plot the original, located data and corrected pulse
fig, ax = subplots(2,sharex=True)
ax[0].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
ax[0].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(real).data)
ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(imag).data)
ax[0].set_title('Original Waveform and Located Waveform')

ax[1].plot(correctedData.getaxis('t'),correctedData.runcopy(real).data)
ax[1].plot(correctedData.getaxis('t'),correctedData.runcopy(imag).data)
ax[1].set_title('Corrected Waveform')


pys.show()


