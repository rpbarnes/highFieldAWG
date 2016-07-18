""" 
This code puts out various amplitude steps so that we can calculate something of a transfer function.
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
amplitudeRange = arange(0.3,.6,0.01)
""" 
This code puts out various amplitude steps so that we can calculate something of a transfer function.
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
amplitudeRange = arange(0.03,.1,0.01)
amplitudeRange = arange(0.5,.6,0.01)
amplitudeRange[1]=0.03
# start at 0.27 and go to 
timeAxis = r_[0:400e-9:1e-9]
waveList = []
for amplitude in amplitudeRange:
	amp = zeros([len(timeAxis)])
	amp[:] = amplitude
	waveList.append(nddata(amp).rename('value','t').labels('t',timeAxis))
wave = concat(waveList,'t')
wave.labels('t',linspace(0,len(wave.data)*1e-9,len(wave.data)))
print 'pulse is %0.1f ns long'%len(wave.data)
print len(amplitudeRange)




ion()
plot(wave.getaxis('t'),wave.runcopy(real).data)
plot(wave.getaxis('t'),wave.runcopy(imag).data)
plot(wave.getaxis('t'),wave.runcopy(abs).data)
title('Amplitude Steps')
draw()


sram = p.wave2sram(wave.data)
sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
p.fpga.dac_run_sram_slave(sram,False)

# start at 0.27 and go to 
timeAxis = r_[0:400e-9:1e-9]
waveList = []
for amplitude in amplitudeRange:
	amp = zeros([len(timeAxis)])
	amp[:] = amplitude
	waveList.append(nddata(amp).rename('value','t').labels('t',timeAxis))
wave = concat(waveList,'t')
wave.labels('t',linspace(0,len(wave.data)*1e-9,len(wave.data)))
print 'pulse is %0.1f ns long'%len(wave.data)




ion()
plot(wave.getaxis('t'),wave.runcopy(real).data)
plot(wave.getaxis('t'),wave.runcopy(imag).data)
plot(wave.getaxis('t'),wave.runcopy(abs).data)
title('Amplitude Steps')
draw()


sram = p.wave2sram(wave.data)
sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
p.fpga.dac_run_sram_slave(sram,False)

