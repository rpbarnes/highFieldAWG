"""

I measure the amplitude adn phase response of the high field system and now generate a lookup table for the output information

"""

import matlablike as pys
import csv

# Write data tuple to csv#{{{
def dataToCSV(dataWriter, fileName,flag = 'wb'):
    """
    Write a tuple of data to a csv. You need to pass the tuple to write to the csv.

    args:
    dataWriter - tuple of data. eg. zip(list(enhancementPowerSeries.getaxis('power')),list(enhancementPowerSeries.data),list(enhancementSeries.getaxis('expNum'))) 
    fileName - string of the full filename
    """
    with open(fileName,flag) as csvFile:
        writer = csv.writer(csvFile,delimiter =',')
        writer.writerows(dataWriter)
#}}}


close('all')
fullPath = r'e:\\'
outputData = 'AWG_phase_amplitude_array_196.4911GHZ.dat'
loadTrace = True
debug = True
reCalcData = True
#inputData = 'PulseAmplitudeCalibrationDigitalAmplitudes.csv'
### make data set to throw all data#{{{
resolution = 64
ampArray = linspace(.3,.41,resolution)
phaseArray = linspace(-pi/16.,pi/16.,resolution)

### load in the data sets.#{{{
# the output data in the .dat file
if loadTrace:
    openFile = open(fullPath + outputData,'r+')
    lines = openFile.readlines()
    lines.pop(0)
    time = []
    data = []
    for line in lines:
        line = line.split('\n')[0].split('  ')
        line = filter(None,line)
        time.append(float(line.pop(0))) # it looks that the first item is always the time increment
        indData = []
        for item in line:
            item = item.split(' ')
            indData.append(float(item[0]) + 1j*float(item[1]))
        data.append(pys.nddata(array(indData)).rename('value','amp').labels('amp',ampArray))
    output = pys.concat(data,'t').labels('t',array(time))

## the input data
#openFile = open(fullPath + inputData,'r+')
#lines = openFile.readlines()
#lines.pop(0)
#amplitudeData = []
#for line in lines:
#    line = line.split(',')
#    amplitudeData.append(float(line[0]))#}}}

start = 680e-9
width = 200e-9
bufferVal = 25e-9
# now calculate the phase and amplitude of each time increment.
if reCalcData:
    data = pys.ndshape([len(ampArray),len(phaseArray)],['amp','phase'])
    data = data.alloc(dtype='complex')
    data.labels(['amp','phase'],[ampArray,phaseArray])#}}}
    expOutput = []
    pys.figure()
    pys.plot(output['amp',0])
    for countAmp,amp in enumerate(ampArray):
        for countPhase,phase in enumerate(phaseArray):
            currSlice = output['amp',countAmp,'t',lambda x: logical_and(x > start + width*countPhase + bufferVal, x < start + width*(countPhase+1) - bufferVal)]
            data['amp',countAmp,'phase',countPhase] = currSlice.copy().mean('t').data
            if debug:
                pys.plot(currSlice,'r')
    pys.title('Pulse trace')
    pys.xlabel('time (us)')
    pys.ylabel('amplitude')
    pys.tight_layout()
    pys.savefig('pulseTrace.png')


pys.figure()
pys.image(data)
pys.legend(loc=4)
pys.title('Phase Lookup Table')
pys.xlabel('digital phase')
pys.ylabel('digital amplitude')
pys.tight_layout()
pys.savefig('digPhaseAmpOutPhase.png')

pys.figure()
pys.image(data.runcopy(abs))
pys.legend(loc=4)
pys.title('Amp Lookup Table')
pys.xlabel('digital phase')
pys.ylabel('digital amplitude')
pys.tight_layout()
pys.savefig('digPhaseAmpOutAmp.png')


pys.show()


# save things to csv
#dataWriter = [('real','imag','digAmp')] + zip(list(expDigComp.runcopy(real).data),list(expDigComp.runcopy(imag).data),list(expDigComp.getaxis('digAmp'))) 
#dataToCSV(dataWriter,'outputAmplitude.csv')
#dataWriter = [('phase (rad)','digAmp')] + zip(list(outputPhase.runcopy(real).data),list(outputPhase.getaxis('digAmp'))) 
#dataToCSV(dataWriter,'outputPhase.csv')


