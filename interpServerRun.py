
"""
this ois going to use the calibration file to produce an am pulse and let the server control the iterration.

"""

import matlablike as pys
from pylab import *
import time
from scipy import interpolate
import socket
import synthesize as s
try:
    p
except:
    p = s.pulsegen()

ion()
pys.close('all')
FPGAComp = True
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
makePlots = False

### Server stuff
sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('128.111.114.94',9000)) 
sock.listen(1)


### Input Waveform
chirpLength = 10e-6
timeResolution = 4e-9
convolveOutput=False
timeAxis = pys.r_[0:chirpLength+timeResolution:timeResolution]
freqOffset = 5e6
freqOffsetArray = pys.r_[-freqOffset:freqOffset: 21j]
freqWidth = 2e6
#freqWidth /= 16.
rate = 2*freqWidth/chirpLength
# this is the phase modulation
phaseModulation = pys.nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
# this is the frequency modulation
chirp = pys.nddata(exp(1j*phaseModulation.data)).rename('value','t').labels(['t'],[timeAxis])
ampModulation = pys.nddata(sin(pi/chirpLength*timeAxis)).rename('value','t').labels('t',timeAxis)

print "Server is live"
while True:
    for count,freqOffset in enumerate(freqOffsetArray):
        planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
        waveform = chirp*planeWave*ampModulation
        ### Add server connection here
        conn,addr = sock.accept()
        close('all')
        print 'Got connection from ', addr
        print 'Running lookup and synthesis'
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
        if makePlots:
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


        if makePlots:
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
            sram = p.wave2sram(array(list(newWave.data)+[1.0]*16))
            sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
            p.fpga.dac_run_sram_slave(sram,False)
            print "synthesized waveform"
            #conn.send('Waveform Synthesized')

