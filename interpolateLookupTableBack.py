"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

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
lookupTable.data /= lookupTable.data.max()
preservedTable = lookupTable.copy()
lookupTable = lookupTable['phase',lambda x: abs(x) < 10]


### Input Waveform
chirpLength = 10e-6
timeAxis = pys.r_[0:chirpLength:1e-9]
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

for countFreq,freqOffset in enumerate(freqOffsetArray):
    start = time.time()
    close('all')
    planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
    waveform = chirp*planeWave*ampModulation

    #### Plot the original uncorrected pulse
    #fig, ax = subplots(2,sharex=True,figsize=(14,12))
    #ax[0].plot(chirp.getaxis('t'),chirp.runcopy(real).data)
    #ax[0].plot(chirp.getaxis('t'),chirp.runcopy(imag).data)
    #ax[0].set_title('Chirp Pulse Uncorr')

    #ax[1].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
    #ax[1].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
    #ax[1].set_title('Chirp with Frequency Offset and Amp Modulation Uncorr')

    ### Scale the lookup table to go from -1 to 1 for real and imaginary
    figure()
    pys.image(lookupTable)
    ### find the waveform
    locatedData = []
    phaseLowBounds = []
    phaseHighBounds = []
    ampList =[]
    phaseList =[]
    phase=0
    amp=0.4
    start = time.time()
    for count,dataVal in enumerate(waveform.data):
        #print "looking about phase %0.2f and amp %0.2f"%(phase,amp)
        if boundTable:
            lowBound=phase-180./16
            highBound=phase+180./16
            ampLowBound=amp-0.1
            ampHighBound=amp+0.1
        else:
            lowBound = -179
            highBound = 179
            ampLowBound = 0.3
            ampHighBound = 1.
        # If either low or high bound you need to stitch together the tables.
        if lowBound < -180.:
            lowBound = 360+lowBound
            table1 = lookupTable['phase',lambda x: x >= lowBound].copy()
            phase1 = table1.getaxis('phase')
            table2 = lookupTable['phase',lambda x: x <= highBound].copy()
            phase2 = table2.getaxis('phase')
            currTable = pys.concat([table1,table2],'phase').labels('phase',array(list(phase1)+list(phase2)))
            currTable -= dataVal
            print "found edge case low bound is now %0.2f and high bound is %0.2f"%(lowBound,highBound)
        elif highBound > 180:
            highBound = highBound-360
            table1 = lookupTable['phase',lambda x: x >= lowBound].copy()
            phase1 = table1.getaxis('phase')
            table2 = lookupTable['phase',lambda x: x <= highBound].copy()
            phase2 = table2.getaxis('phase')
            currTable = pys.concat([table1,table2],'phase').labels('phase',array(list(phase1)+list(phase2)))
            currTable -= dataVal
            print "found edge case low bound is now %0.2f and high bound is %0.2f"%(lowBound,highBound)
        else:
            currTable = lookupTable['phase',lambda x: logical_and(x >= lowBound, x <= highBound)].copy() - dataVal
            currTable = currTable['amp',lambda x: logical_and(x>=ampLowBound,x<=ampHighBound)] 
        phaseLowBounds.append(lowBound)
        phaseHighBounds.append(highBound)
        minimaIndex = unravel_index(argmin(currTable.runcopy(abs).data),shape(currTable.data)) 
        amp = lookupTable.getaxis('amp')[minimaIndex[0]]
        phase = lookupTable.getaxis('phase')[minimaIndex[1]]
        locatedData.append(lookupTable.data[minimaIndex])
        ampList.append(amp)
        phaseList.append(phase)
    print "Search loop for waveform took: ",time.time()-start
    print "Size of search table is: ",shape(currTable.data)
    pys.plot(array(phaseList),array(ampList),'o',markersize=5)
    pys.plot(array(phaseList),array(ampList),'--')
    locatedData = pys.nddata(array(locatedData)).rename('value','t').labels('t',waveform.getaxis('t'))
    interpolatedWaveform = pys.nddata(array(ampList)*exp(1j*(pi*array(phaseList)/180))).rename('value','t').labels('t',waveform.getaxis('t'))
    smoothedData = correctedData.copy().convolve('t',5e-9)
    ### Calculate the phase and amplitude jumps.
    phases = []
    amps = []
    for count in range(len(phaseList)-1):
        phases.append(phaseList[count]-phaseList[count+1])
        amps.append(ampList[count]-ampList[count+1])
    figure()
    plot(waveform.getaxis('t')[0:-1],array(phases),label='phaseDiff')
    plot(waveform.getaxis('t')[0:-1],array(amps),label='ampDiff')
    legend()
    title('Phase and amplitude Jumps')
    ### Keep track of the phase bounds 
    figure()
    plot(waveform.getaxis('t'),array(phaseLowBounds),label='lowBound')
    plot(waveform.getaxis('t'),array(phaseHighBounds),label='highBound')
    plot(waveform.getaxis('t'),array(phaseList),label='phase')
    legend()
    title('Phase and bounds')

    ### Now go through and unwrap the -pi/16 to pi/16 phase jumps at x band, so that this waveform moves smoothly.
    phaseUnwrapped = unwrap(array(phaseList),discont=180./16)
    unwrappedInterpolatedWaveform = pys.nddata(array(ampList)*exp(1j*(pi*phaseUnwrapped/180))).rename('value','t').labels('t',waveform.getaxis('t'))
    # Find the 200 GHz waveform
    uPhase = arctan2(real(unwrappedInterpolatedWaveform.data),imag(unwrappedInterpolatedWaveform.data))*180/pi
    uAmp = abs(unwrappedInterpolatedWaveform.data)
    u200Wf = []
    # do a 2d interpolation - not really a 2d interpolation but something home brewed...
    for count in range(len(uPhase)):
        phaseArg = argmin(abs(preservedTable.getaxis('phase')-uPhase[count]))
        ampArg = argmin(abs(preservedTable.getaxis('amp')-uAmp[count]))
        u200Wf.append(preservedTable['phase',phaseArg,'amp',ampArg].data)
    u200Wf = pys.nddata(array(u200Wf)).rename('value','t').labels('t',waveform.getaxis('t'))
        







    ### Plot the original, located data and interpolated pulse
    fig, ax = subplots(3,sharex=True,figsize=(14,12))
    ax[0].plot(waveform.getaxis('t'),waveform.runcopy(real).data)
    ax[0].plot(waveform.getaxis('t'),waveform.runcopy(imag).data)
    ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(real).data)
    ax[0].plot(locatedData.getaxis('t'),locatedData.runcopy(imag).data)
    ax[0].set_title('200 GHz: Original Waveform and Located Waveform')


    ax[1].plot(waveform.getaxis('t'),unwrap(arctan2(waveform.runcopy(imag).data,waveform.runcopy(real).data))/16.)
    ax[1].plot(locatedData.getaxis('t'),unwrap(arctan2(locatedData.runcopy(imag).data,locatedData.runcopy(real).data))/16.)
    ax[1].plot(interpolatedWaveform.getaxis('t'),unwrap(arctan2(interpolatedWaveform.runcopy(imag).data,interpolatedWaveform.runcopy(real).data))/16.)

    ax[2].plot(interpolatedWaveform.getaxis('t'),interpolatedWaveform.runcopy(real).data)
    ax[2].plot(interpolatedWaveform.getaxis('t'),interpolatedWaveform.runcopy(imag).data)
    ax[2].plot(unwrappedInterpolatedWaveform.getaxis('t'),unwrappedInterpolatedWaveform.runcopy(real).data)
    ax[2].plot(unwrappedInterpolatedWaveform.getaxis('t'),unwrappedInterpolatedWaveform.runcopy(imag).data)
    #ax[2].plot(smoothedData.getaxis('t'),smoothedData.runcopy(real).data)
    #ax[2].plot(smoothedData.getaxis('t'),smoothedData.runcopy(imag).data)
    ax[2].set_title('12 GHz Input Waveform')

    # synthesize the waveform
    #wave = p.make_highres_waveform([('rect',0,chirpLength+1e-6)],resolution = 1e-9)
    #for loop in range(len(smoothedData.data)-1):
    #	for constCount in range(1):
    #		wave.data[constCount+(loop*1)] = smoothedData.data[loop]
    #sram = p.wave2sram(wave.data)
    #sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
    #p.fpga.dac_run_sram_slave(sram,False)
    #print "Running Frequency %0.1f and count %i"%(freqOffset,countFreq)
    #print 'I take ',time.time() - start,' (s) to complete'
show()
