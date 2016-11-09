"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

this will eval the positive (right) and negative (left) areas (relative to current value)  of the phase profile separately then pick the step that results in the least phase change.

"""

import matlablike as pys
from pylab import *
import time
from scipy import interpolate
import csv

try:
    import labrad
    FPGAComp=False
except:
    FPGAComp=False

if FPGAComp:
    import synthesize as s
    try:
    	p
    except:
    	p = s.pulsegen()
    
ion()

pys.close('all')

lookupTableFile = 'LookupTable.h5/phase512m180dt180dAmp128p4t1QCW' # make sure to set amp & phase axis appropriately
lookupTable = pys.nddata_hdf5(lookupTableFile)
ampAxis = pys.linspace(.4,1.,128)
phaseAxis = pys.linspace(-180,180,512)
lookupTable.labels('amp',ampAxis)
lookupTable.labels('phase',phaseAxis)
# normalize the lookuptable
ampNorTable = lookupTable['amp',lambda x: x >= 0.95].copy()
lookupTable.data /= ampNorTable.runcopy(abs).data.min()
phaseStep = 180./16
ampStep=0.03
phaseLow = -180.
phaseHigh = 180.

goUp=False
goDown=False
unBound=False
boundTable = True


### Input Waveform
chirpLength = 3e-6
timeResolution = 5e-9
convolveOutput=False
timeAxis = pys.r_[0:chirpLength+timeResolution:timeResolution]
freqOffset = 0e6
freqOffsetArray = pys.r_[-freqOffset:freqOffset: 1j]
freqWidth = 5e6
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
    if count == 0:
        print "finding first index"
        currTable = abs(lookupTable.copy() - dataVal)
        minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
        currIndex = minimaIndex
	currAmp = lookupTable.getaxis('amp')[minimaIndex[0]] 
	currPhase = lookupTable.getaxis('phase')[minimaIndex[1]]
        ampList.append(currAmp)
        phaseList.append(currPhase)
        foundWaveform.append(lookupTable.data[minimaIndex])
    else:
        print "%i / %i"%(count+1,totalLength), "looking about index ", currIndex
        if goUp:
            currTable = abs(lookupTable.copy() - dataVal)
            if (currIndex[1]+maxIndexShift)>=(len(lookupTable.getaxis('phase'))-1): # If we're at the edge of the array let it roll to the other side.
                currIndex = (currIndex[0],0)
            currTable = currTable['phase',currIndex[1]:currIndex[1]+maxIndexShift]
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = (minimaIndex[0],minimaIndex[1]+currIndex[1])                        # you cut the phase indecies by currIndex, now add it back
        elif goDown:
            currTable = abs(lookupTable.copy() - dataVal)
            if (currIndex[1]-maxIndexShift)<=0: # If we're at the edge of the array let it roll to the other side.
                currIndex = (currIndex[0],len(lookupTable.getaxis('phase'))-1)
            currTable = currTable['phase',currIndex[1]-maxIndexShift:currIndex[1]]
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = (minimaIndex[0],minimaIndex[1]+(currIndex[1]-maxIndexShift))                        # you cut the phase indecies by currIndex, now add it back
        elif unBound:
            currTable = abs(lookupTable.copy() - dataVal)
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = minimaIndex
            currPhase = currTable.getaxis('phase')[currIndex[1]]
            currAmp = currTable.getaxis('amp')[currIndex[0]]
            waveSlice = lookupTable.data[currIndex]
        elif boundTable:
            # Set phase and amplitude bounds on the table
            if currPhase+phaseStep > phaseHigh: # need to add the lower phase to the table
                # cycle around
                phaseDiff = currPhase+phaseStep - phaseHigh
                phaseDiff += phaseLow 
                highTable = lookupTable['phase',lambda x: x > currPhase-phaseStep]
                lowTable = lookupTable['phase',lambda x: x < phaseDiff]
                currTable = pys.concat([lowTable,highTable],'phase').labels('phase',array(list(lowTable.getaxis('phase'))+list(highTable.getaxis('phase'))))
                currTable = currTable['amp',lambda x: logical_and(x > currAmp-ampStep,x < currAmp+ampStep)]
                saveTable = currTable.copy()
                print "Cycling around the high side of phase axis"
            elif currPhase-phaseStep < phaseLow: # need to add the higher phase to the table
                # cycle around
                phaseDiff = currPhase-phaseStep - phaseLow
                phaseDiff += phaseHigh 
                highTable = lookupTable['phase',lambda x: x > phaseDiff]
                lowTable = lookupTable['phase',lambda x: x < currPhase+phaseStep]
                currTable = pys.concat([lowTable,highTable],'phase').labels('phase',array(list(lowTable.getaxis('phase'))+list(highTable.getaxis('phase'))))
                currTable = currTable['amp',lambda x: logical_and(x > currAmp-ampStep,x < currAmp+ampStep)]
                saveTable = currTable.copy()
                print "Cycling around the low side of phase axis"
            else:
                currTable = lookupTable['phase',lambda x: logical_and(x > currPhase-phaseStep,x < currPhase+phaseStep)]
                currTable = currTable['amp',lambda x: logical_and(x > currAmp-ampStep,x < currAmp+ampStep)]
                saveTable = currTable.copy()
            currTable = abs(currTable - dataVal)
            minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
            currIndex = minimaIndex
            currPhase = currTable.getaxis('phase')[currIndex[1]]
            currAmp = currTable.getaxis('amp')[currIndex[0]]
            waveSlice = saveTable.data[currIndex]


        ampList.append(currAmp)                   # calculate new amplitude and phase values
        print currPhase
        phaseList.append(currPhase)
        foundWaveform.append(waveSlice)

print "Loop took %0.2f seconds"%(time.time()-start)
foundWaveform = pys.nddata(array(foundWaveform)).rename('value','t').labels('t',waveform.getaxis('t'))
phaseList = array(phaseList)
ampList = array(ampList)

figure()
pys.plot(foundWaveform.runcopy(real),'b.',alpha=0.3,label='located')
pys.plot(foundWaveform.runcopy(real),'b--',alpha=0.3)
pys.plot(waveform.runcopy(real),'bo',alpha=0.3,label='target')
pys.plot(foundWaveform.runcopy(imag),'r.',alpha=0.3)
pys.plot(foundWaveform.runcopy(imag),'r--',alpha=0.3)
pys.plot(waveform.runcopy(imag),'ro',alpha=0.3)
legend()

# track phase and amplitude
figure()
pys.image(lookupTable)
plot(phaseList,ampList,'g.',alpha=0.3,markersize=10)
plot(phaseList,ampList,'k--',alpha=0.5)
ylim(ampList.min(),ampList.max())
xlim(phaseList.min(),phaseList.max())

xbandWave = pys.nddata(array(ampList)*exp(1j*array(phaseList)*pi/180)).rename('value','t').labels('t',waveform.getaxis('t'))
if convolveOutput:
    toSynthesize=xbandWave.copy().convolve('t',timeResolution*2)
else:
    toSynthesize=xbandWave.copy()
# splice this into an appropriately sampled waveform
if FPGAComp:
    wave=p.make_highres_waveform([('delay',toSynthesize.getaxis('t').max())])
    wave.ft('t',shift=True)
    toSynthesize.ft('t',shift=True)
    dataList = [wave['t',lambda x: x <= toSynthesize.getaxis('t').min()],toSynthesize,wave['t',lambda x: x >= toSynthesize.getaxis('t').max()]]
    newWave = pys.concat(dataList,'t')
    newWave = newWave['t',1:-1]
    newWave.labels('t',wave.getaxis('t'))
    toSynthesize.ift('t',shift=True)
    newWave.ift('t',shift=True)


figure()
pys.plot(xbandWave,label='real Rough')
pys.plot(xbandWave.runcopy(imag),label='imag Rough')
pys.plot(toSynthesize,label='real Smooth')
pys.plot(toSynthesize.runcopy(imag),label='imag Smooth')
if FPGAComp:
    pys.plot(newWave,label='real SentToDac')
    pys.plot(newWave.runcopy(imag),label='imag SentToDac')
legend()
title('x band waveform')

figure()
pys.plot(xbandWave.getaxis('t'),arctan2(real(xbandWave.data),imag(xbandWave.data)))
title('x band phase')
show()


### Synthesize the waveform
if FPGAComp:
    #sram = p.wave2sram(array(list(newWave.data)+list(newWave.data)+list(newWave.data)))
    sram = p.wave2sram(newWave.data)
    sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
    p.fpga.dac_run_sram_slave(sram,False)
    print "synthesized waveform"

### Items to save
def writeCSV(fileName,dataWriter):
    csvfile = open(fileName,'w')
    writer = csv.writer(csvfile, delimiter=',',lineterminator='\n',)
    writer.writerows(dataWriter)
# Xband waveform toSynthesize
dataWriter = [('time (s)','real','imag')]+zip(list(toSynthesize.getaxis('t')),list(toSynthesize.runcopy(real).data),list(toSynthesize.runcopy(imag).data))
fileName = 'xBandWave_%0.0fMHzOffset_%0.0fMHzWidth_%0.0fusLength.csv'%(freqOffset/1e6,freqWidth/1e6,chirpLength*1e6)
writeCSV(fileName,dataWriter)
# 200 GHz waveform target 'waveform' and found 'foundWaveform'
dataWriter = [('time (s)','real','imag')]+zip(list(waveform.getaxis('t')),list(waveform.runcopy(real).data),list(waveform.runcopy(imag).data))
fileName = '200GHzTargetWave_%0.0fMHzOffset_%0.0fMHzWidth_%0.0fusLength.csv'%(freqOffset/1e6,freqWidth/1e6,chirpLength*1e6)
writeCSV(fileName,dataWriter)
dataWriter = [('time (s)','real','imag')]+zip(list(foundWaveform.getaxis('t')),list(foundWaveform.runcopy(real).data),list(foundWaveform.runcopy(imag).data))
fileName = '200GHzFoundWaveform%0.0fMHzOffset_%0.0fMHzWidth_%0.0fusLength.csv'%(freqOffset/1e6,freqWidth/1e6,chirpLength*1e6)
writeCSV(fileName,dataWriter)

# phase and amplitude steps 'phaseList' and 'ampList'
dataWriter = [('phase','amp')]+zip(phaseList,ampList)
fileName = 'XbandPhaseAndAmpSteps%0.0fMHzOffset_%0.0fMHzWidth_%0.0fusLength.csv'%(freqOffset/1e6,freqWidth/1e6,chirpLength*1e6)
writeCSV(fileName,dataWriter)

fileName = 'lookupTable.txt'
#openFile = open(fileName,'w')
#openFile.write(list(lookupTable.getaxis('phase')))
#for count,amp in enumerate(lookupTable.getaxis('amp')):
#    listToWrite=[[amp],list(lookupTable['amp',i].data)]
#    listToWrite = [item for sublist in listToWrite for item in sublist]
#    openFile.write(listToWrite)
#savetxt(fileName,lookupTable.data,delimiter=',',fmt=%0.3f)


