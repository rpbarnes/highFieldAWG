"""

This is to correct for the non linearity of the multiplier circuits via interpolation of a previous measurement.

"""
import matlablike as pys
import synthesize as s
close('all')

def pullCsvData(fileName,numberOfCols,popHeader=True,delimiter = '\n'):#{{{
    """ This reads float data from the columns of a csv file """
    openFile = open(fileName,'r+')
    lines = openFile.readlines()
    if len(lines) == 1:
        lines = lines[0].split(delimiter)
    if popHeader:
        lines.pop(0)
    dataArray = pys.zeros((len(lines),numberOfCols))
    for count,line in enumerate(lines):
        line = line.split(',')
        for column in range(numberOfCols):
            dataArray[count,column] = float(line[column])
    return dataArray#}}}

try:
	p
except:
	p = s.pulsegen()
close('all')

outputDataFile = 'outputAmplitude.csv'
pys.ion()

# constants
dynamicRangeMin = 0.3 # This is where the modulation starts.
dynamicRangeMax = 0.41
freqOffset = 10e6 #Hz
freqWidth = 10e6 # Hz, I run plus and minus this width. This is also the width at 200 GHz, I scale approprately in code.
chirpLength = 10e-6 # seconds
amplitudeScalingFactor = 0.37

wave = p.make_highres_waveform([('rect',0,chirpLength+1e-6)],resolution = 1e-9)


outputData = pullCsvData(outputDataFile,3)
outputData = pys.nddata(outputData[:,0]+1j*outputData[:,1]).rename('value','digAmp').labels('digAmp',outputData[:,2])
# take only what we can use and set to full scale
outputClean = outputData['digAmp',lambda x: logical_and(x>=dynamicRangeMin,x<=dynamicRangeMax)]
# Clean up the amplitude
outputAmp = outputClean.runcopy(abs)
outputAmp.data -= outputAmp.data.min()
outputAmp /= outputAmp.data.max()
pys.figure()
pys.plot(outputData.runcopy(abs))
pys.plot(outputAmp.runcopy(abs))
# calculate the phase roll at given amp, unwrap the roll so we can interpolate.
outputClean.data = arctan2(outputClean.runcopy(imag).data,outputClean.runcopy(real).data)
outputClean.data = unwrap(outputClean.data)
pys.figure()
pys.plot(outputClean,'r.')
pys.title('phase roll')

timeAxis = r_[0:chirpLength:1e-9]
freqWidth /= 16.
rate = 2*freqWidth/chirpLength
# this is the phase modulation
modulation = pys.nddata(2*pi*(-freqWidth*timeAxis + rate/2*timeAxis**2)).rename('value','t').labels(['t'],[timeAxis])
# this is the frequency modulation
chirp = pys.nddata(exp(1j*modulation.data)).rename('value','t').labels(['t'],[timeAxis])
planeWave = pys.nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])

# amplitude modulation
sinMod = pys.nddata(sin(pi/chirpLength*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
# the corrected amplitude
correctedDigAmp = nddata(interp(sinMod.data,outputAmp.data,outputAmp.getaxis('digAmp'))).rename('value','t').labels('t',timeAxis)
# the phase roll for our amplitude input
phaseRoll = nddata(interp(correctedDigAmp.data,outputClean.getaxis('digAmp'),outputClean.data)).rename('value','t').labels('t',timeAxis)
pys.figure()
pys.plot(phaseRoll)
pys.title('phase roll for amplitude input')

# now correct the phase of the chirp pulse
correctedChirp = chirp.copy()
correctedChirp.data = chirp.data*exp(1j*phaseRoll.data)

# plot the chirp before frequency offset
pys.figure()
pys.plot(sinMod)
pys.plot(chirp)
pys.plot(correctedDigAmp)
pys.plot(correctedChirp)

toSynthesize = correctedChirp*correctedDigAmp
pys.figure()
pys.plot(toSynthesize)

wave['t',0:len(toSynthesize.data)] = toSynthesize.data

pys.show()
