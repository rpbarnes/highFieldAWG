"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

This will restrict the lookup search trajectory to only look at the next series of positive index from the current phase index where the series is constricted by a pi/16 phase rotation.

"""

import matlablike as pys
#import labrad
#import synthesize as s
from pylab import *
import time
from scipy import interpolate
#try:
#	p
#except:
#	p = s.pulsegen()
#
ion()

pys.close('all')

boundTable = False
lookupTableFile = 'LookupTable.h5/phase512amp128'
lookupTable = pys.nddata_hdf5(lookupTableFile)
preservedTable = lookupTable.copy()
lookupTable = lookupTable['amp',lambda x: x < .6]
lookupTable.data /= lookupTable.data.max()
maxIndexShift=5
goUp=False
if goUp:
    goDown = False
else:
    goDown = True


### Input Waveform
chirpLength = 10e-6
timeAxis = pys.r_[0:chirpLength:20e-9]
freqOffset = 0e6
freqOffsetArray = pys.r_[-freqOffset:freqOffset: 1j]
freqWidth =    10e6
#freqWidth /= 16.
rate = 2*freqWidth/chirpLength
# this is the phase modulation
phaseModulation = pys.nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
# this is the frequency modulation
chirp = pys.nddata(exp(1j*phaseModulation.data)).rename('value','t').labels(['t'],[timeAxis])
ampModulation = pys.nddata(sin(pi/chirpLength*timeAxis)).rename('value','t').labels('t',timeAxis)

### this goes in the loop of things.
planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
waveform = chirp*planeWave*ampModulation

### Find the minima
start = time.time()
totalLength = len(waveform.data)
phaseList = []                                              # Input amplitude and phase lists.
ampList = []
foundWaveform = []
for count,dataVal in enumerate(waveform.data):
    tempThreshold = threshold
    if count == 0:
        print "finding first index"
        currTable = abs(lookupTable.copy() - dataVal)
        minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
        currIndex = minimaIndex
        ampList.append(lookupTable.getaxis('amp')[minimaIndex[0]])
        phaseList.append(lookupTable.getaxis('phase')[minimaIndex[1]])
        foundWaveform.append(lookupTable.data[minimaIndex])
    else:
        print "%i / %i"%(count+1,totalLength), "looking about index ", currIndex
        currTable = abs(lookupTable.copy() - dataVal)
        if goUp:
            if (currIndex[1]+maxIndexShift)>=(len(lookupTable.getaxis('phase'))-1): # If we're at the edge of the array let it roll to the other side.
                currIndex = (currIndex[0],0)
            currTable = currTable['phase',currIndex[1]:currIndex[1]+maxIndexShift]
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = (minimaIndex[0],minimaIndex[1]+currIndex[1])                        # you cut the phase indecies by currIndex, now add it back
        if goDown:
            if (currIndex[1]-maxIndexShift)<=0: # If we're at the edge of the array let it roll to the other side.
                currIndex = (currIndex[0],len(lookupTable.getaxis('phase'))-1)
            currTable = currTable['phase',currIndex[1]-maxIndexShift:currIndex[1]]
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = (minimaIndex[0],minimaIndex[1]+(currIndex[1]-maxIndexShift))                        # you cut the phase indecies by currIndex, now add it back

        ampList.append(lookupTable.getaxis('amp')[currIndex[0]])                   # calculate new amplitude and phase values
        phaseList.append(lookupTable.getaxis('phase')[currIndex[1]])
        foundWaveform.append(lookupTable.data[currIndex])

print "Loop took %0.2f seconds"%(time.time()-start)
foundWaveform = pys.nddata(array(foundWaveform)).rename('value','t').labels('t',waveform.getaxis('t'))
phaseList = array(phaseList)
ampList = array(ampList)

figure()
pys.plot(foundWaveform)
pys.plot(waveform)

# track phase and amplitude
figure()
pys.image(lookupTable)
plot(phaseList,ampList,'g.',markersize=10)
plot(phaseList,ampList,'k--',alpha=0.5)
ylim(ampList.min(),ampList.max())
xlim(phaseList.min(),phaseList.max())

xbandWave = pys.nddata(array(ampList)*exp(1j*array(phaseList)*pi/180)).rename('value','t').labels('t',waveform.getaxis('t'))
figure()
pys.plot(xbandWave,label='real')
pys.plot(xbandWave.runcopy(imag),label='imag')
legend()
title('x band waveform')

figure()
pys.plot(xbandWave.getaxis('t'),arctan2(real(xbandWave.data),imag(xbandWave.data)))
title('x band phase')
show()

