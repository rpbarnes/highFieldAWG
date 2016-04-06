""" 
This code makes a chirp pulse defined by the frequency width and the center frequency relative to the carrier as well as the length of the pulse.

The chirp plays at the beginning of the pulse followed by 1's

"""
import labrad
import synthesize as s
from matlablike import *

try:
	p
except:
	p = s.pulsegen()
close('all')
# constants
freqOffsetArray = arange(-10,10.5,0.5)*1e6
amplitudeScalingFactor = 1
freqOffsetArray /= 16.
### make the BIP Pulse
BIPLength = 6.9e-6
fileName = 'BIP_1382_250_15.dat'
amplitude = 1.0
openFile = open(fileName,'r+')
lines = openFile.readlines()
times = lines[0].split('\n')[0].split('  ')
phaseVals = lines[1].split('\n')[0].split('  ')
phaseList = []
timeList = []
for i in range(len(phaseVals)):
	try:
		phaseList.append(float(phaseVals[i]))
		timeList.append(float(times[i]))
	except:	
		print 'crap'
timeAxisHighRes = pys.r_[0:BIPLength:len(timeList)*1j]
timeAxisToSynth = pys.r_[0:BIPLength:1e-9]
pulsePhaseHighRes = pys.nddata(pys.array(phaseList)).rename('value','t').labels('t',timeAxisHighRes)
# convert to rad
pulsePhaseHighRes*=pys.pi/180.
# knock down to 12 Ghz waveform
pulsePhaseHighRes/=16.
pulsePhaseToSynth = pys.nddata(pys.interp(timeAxisToSynth,timeAxisHighRes,pulsePhaseHighRes.data)).rename('value','t').labels('t',timeAxisToSynth)
pys.ion()
pys.plot(pulsePhaseHighRes)
pys.plot(pulsePhaseToSynth,'.',alpha=.4)
BIPPulse = pulsePhaseToSynth.copy()
BIPPulse.data = amplitude*pys.exp(1j*pulsePhaseToSynth.data)

# make wave and scale amplitude of rectangular pulse
for freqOffset in freqOffsetArray:
	raw_input('Press Enter to run %0.3f'%freqOffset)
	close('all')
	wave = p.make_highres_waveform([('rect',0,BIPLength+1e-6)],resolution = 1e-9)
	wave.data *= amplitudeScalingFactor
	timeAxis = r_[0:BIPLength:1e-9]
	planeWave = nddata(exp(1j*2*pi*freqOffset*timeAxis)).rename('value','t').labels(['t'],[timeAxis])
	# make a copy of the BIP pulse. Call it chirp just because 
	chirp = BIPPulse.copy()
	ion()
	fig, ax = subplots(2,sharex=True)
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(real).data)
	ax[0].plot(chirp.getaxis('t'),chirp.runcopy(imag).data)
	ax[0].set_title('Chirp Pulse')

	chirp*=planeWave
	wave['t',0:len(chirp.data)] = chirp.data
	ax[1].plot(wave.getaxis('t'),wave.runcopy(real).data)
	ax[1].plot(wave.getaxis('t'),wave.runcopy(imag).data)
	ax[1].set_title('Chirp with Frequency Offset')
	draw()
	#


	sram = p.wave2sram(wave.data)
	sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
	p.fpga.dac_run_sram_slave(sram,False)

