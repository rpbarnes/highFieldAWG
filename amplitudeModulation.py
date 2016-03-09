"""

This is to correct for the non linearity of the multiplier circuits via interpolation of a previous measurement.

"""
import matlablike as pys
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


outputDataFile = 'outputAmplitude.csv'

# constants
dynamicRangeMin = 0.3 # This is where the modulation starts.
dynamicRangeMax = 0.4
freqOffset = 10e6 #Hz
freqWidth = 30e6 # Hz, I run plus and minus this width. This is also the width at 200 GHz, I scale approprately in code.
chirpLength = 1e-6 # seconds
amplitudeScalingFactor = 0.37


outputData = pullCsvData(outputDataFile,3)
outputData = pys.nddata(outputData[:,0]+1j*outputData[:,1]).rename('value','digAmp').labels('digAmp',outputData[:,2])
# take only what we can use and set to full scale
outputClean = outputData['digAmp',lambda x: logical_and(x>dynamicRangeMin,x<dynamicRangeMax)]
outputClean -= outputClean.data.min()
outputClean /= outputClean.data.max()

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
# plot the chirp before frequency offset
pys.ion()
pys.plot(sinMod)
pys.plot(chirp)

pys.show()
