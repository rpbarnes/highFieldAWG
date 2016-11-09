"""
I generate a lookup table of the relationship of input amp and phase to output amp and phase. I save it as LookupTable.h5/ampPhaseLookup

"""

### Set plotting parameters.#{{{
fig_width = 5.5
fig_height = 4
fig_size = [fig_width,fig_height] 
tick_size = 15 
fontlabel_size = 'large' 
params = {'backend': 'wxAgg', 
        'lines.markersize' : 1,
        'axes.labelsize': fontlabel_size, 
        'text.fontsize': fontlabel_size, 
        'legend.fontsize': fontlabel_size, 
        'legend.frameon':False,
        'xtick.labelsize': tick_size, 
        'ytick.labelsize': tick_size, 
        'text.usetex': False,
        'figure.figsize': fig_size}

font = {'family' : 'times new roman',
        'weight' : 'bold',
        'size'   : 15}
pys.rc('font',**font)
pys.rc("axes", linewidth=2.0)
pys.rc("lines", markeredgewidth=.5)
pys.rcParams['mathtext.default'] = 'regular'
pys.rcParams.update(params)#}}}

def makeFancyPlot():#{{{
    """ Set various plotting parameters in one function. """
    ax=gca()
    ax.tick_params('both', length=10, width=2, which='major')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', direction='in')
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    tight_layout()#}}}

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
threshold = 0.01
#lookupTable = lookupTable['phase',lambda x: abs(x) < (5/2*180.)/16.]


### Input Waveform
chirpLength = 10e-6
timeAxis = pys.r_[0:chirpLength:5e-9]
freqOffset = 0e6
freqOffsetArray = pys.r_[-freqOffset:freqOffset: 1j]
freqWidth =  3e6
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
        ampVals,phaseVals = where(currTable.data<=tempThreshold) # find values in given range.
        while len(phaseVals) == 0:
            print "Temporarily increasing threshold"
            tempThreshold+=0.01
            ampVals,phaseVals = where(currTable.data<=tempThreshold) # find values in given range.
        phaseIndex = argmin(abs(phaseVals-currIndex[1]))    # get index of phase and amp that is closest to previous value.
        ampIndex = argmin(abs(ampVals-currIndex[0]))
        currIndex = (ampVals[ampIndex],phaseVals[phaseIndex])                   # reset the index
        ampList.append(lookupTable.getaxis('amp')[ampVals[ampIndex]])                   # calculate new amplitude and phase values
        phaseList.append(lookupTable.getaxis('phase')[phaseVals[phaseIndex]])
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

