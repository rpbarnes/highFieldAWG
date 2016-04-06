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
freqOffset = 00e6 #Hz
freqWidthArray = arange(3.1,5.1,.1)*1e6
chirpLengthArray = arange(.5,10.5,.5)*1e-6 # seconds
rate = 2*(3.6/16)*1e6/1e-6
amplitudeScalingFactor = 1

# make wave and scale amplitude of rectangular pulse
wave = p.make_highres_waveform([('rect',0,chirpLength+1e-6)],resolution = 1e-9)
wave.data *= amplitudeScalingFactor

sram = p.wave2sram(wave.data)
sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
p.fpga.dac_run_sram_slave(sram,False)

