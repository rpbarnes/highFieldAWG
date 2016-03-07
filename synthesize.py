from matlablike import * # I like working with the nddata stuff however it's not used very much... This should change.
import os
import sys
import time
import labrad
from labrad.units import V, mV, us, ns, GHz, MHz
from workflow import switchSession as pss #(P)yle(S)witch(S)ession
import scipy.optimize as o
import numpy as np

sys.path.append('C:\Users\hanlab\Desktop\GHz DAC\fpgaTest')
FPGA_SERVER = 'ghz_fpgas'
board = 'Han Lab DAC 1'
DAC_ZERO_PAD_LEN = 16


class pulsegen ():
    ### Import calibration will import calibration parameter from a file if False it wont
    def __init__(self,import_inpcal = False,import_detcal = False):  
        self.res = 1e-11     ### this is the desired resolution of all calibration waveforms ###
        self.cxn = labrad.connect()
        self.switchSession(user='TestUser')
        self.fpga = self.cxn.ghz_fpgas
        self.fpga.select_device(board)
        return

    def switchSession(self,session=None, user=None):
        r'''Switch the current session, using the global connection object'''
        global ses
        if user is None:
            user = ses._dir[1]
        # ses = pss(self.cxn, user, session, useDataVault=True) 
        ses = pss(self.cxn, user, session, useDataVault=False)

    def make_highres_waveform(self,listoftuples,
            resolution = 1e-9,
            verbose = False):
        r'''generates a waveform which is a list of tuples, in the following possible formats:
        ('delay',len)
        ('function',function,taxis)  <-- taxis i either a number (for length), or an array
        ('rect',phase,len)
        phase can be in format number, for degrees, or '+x','x','-y',etc.
        resolution can be specified in seconds.
        use as follows
        wave = self.make_highres_waveform([('delay',100e-9),('rect','x',20e-9),('function',lambda x: sinc(2*pi*x),100e-9),('delay',10e-6-100e-9 - 20e-9 - 100e-9)])
        this generates a rectangle with x phase and a sinc shaped pulse 
        '''
        # if 1e-9 % resolution < 1e-22 or resolution % 1e-9 < 1e-22:
        testfn = lambda x: x+1 # so I can test against the type
        current_waveform = zeros(0,dtype = 'complex128') # start with zero length
        for wavepart in listoftuples:
            #{{{ calculate "thispart" based on what type the tuple is
            if wavepart[0] == 'delay':
                thispart = zeros(int(round(wavepart[1]/resolution)))
            if wavepart[0] == 'function':
                if type(wavepart[1]) is type(testfn):
                    if isscalar(wavepart[2]):
                        t = double(r_[0:wavepart[2]:resolution])-wavepart[2]/2.0
                        t /= t[0]
                    elif type(wavepart[2]) in [list,ndarray]:
                        if len(wavepart[2]) == 2:
                            t = r_[wavepart[2][0]:wavepart[2][1]:resolution]
                        else:
                            raise TypeError('the third element in the tuple',wavepart,'must be a number, or a list or array giving just the start and stop times!')
                    else:
                        raise TypeError('the third element in the tuple',wavepart,'must be a number, or a list or array giving just the start and stop times!')
                    myfn = wavepart[1]
                    thispart = myfn(t)
                else:
                    raise TypeError('The second argument to a function tuple must be a function!')
            if wavepart[0] == 'rect':
                if type(wavepart[1]) is str:
                    phasestring = wavepart[1]
                    negative = 1.
                    if phasestring[0] == '-':
                        negative = -1.
                        phasestring = phasestring[1:]
                    elif phasestring[0] == '+':
                        phasestring = phasestring[1:]
                    if phasestring == 'x':
                        phase = 1.
                    elif phasestring == 'y':
                        phase = 1j
                    else:
                        raise ValueError("I don't understand the phase"+phasestring)
                else:
                    negative = 1.
                    phase = exp(1j*double(wavepart[1])/180.*pi)
                try:
                    thispart = negative * phase * ones(int(round(wavepart[2]/resolution)))
                except IndexError:
                    raise ValueError("You probably entered a tuple of the wrong format --> use something like this ('rect','x',100)")
            if wavepart[0] == 'train':
                # takes a list of lists with [[a1,p1],[a2,p2],...] defining a pulse train with 1 ns steps.
                # resolution of output can still be specified.
                res_factor = int(round(1e-9/resolution))
                if verbose: print wavepart[1]
                zippart = zip(wavepart[1][0],wavepart[1][1])
                if verbose: print zippart
                thispart = ones(len(zippart)*res_factor) * 1j
                for i in range(len(zippart)):
                    negative = 1.
                    amplitude = zippart[i][0]
                    phase = exp(1j*double(zippart[i][1])/180.*pi)
                    try:
                        for j in range(res_factor):
                            thispart[(i*res_factor)+j] = negative * phase * amplitude
                    except IndexError:
                        raise ValueError("You probably entered a tuple of the wrong format --> use something like this ('train',[(1,0.9),(0,90)]), where the first tuple defines the amplitudes, the second one the phase")
            #}}}
            current_waveform = r_[current_waveform,thispart]
        return nddata(current_waveform,[-1],['t'],axis_coords = [resolution*r_[0:size(current_waveform)]]).set_units('t','s')
        # else:
        #     raise ValueError('1 ns needs to be a multiple of your resolution or your resolution needs to be a multiple of 1 ns!')
    #{{{ basic functions
    def check_5char_hex(self,a):
        int(round(a))
        if a > 2**(5*4)-1:
            raise ValueError("too big!!")
        if a < 0:
            raise ValueError("can't be less than zero!")
        return a
    def gen_code(self,opcode,number):
        if opcode not in [1,2,3,4,8,10,12,15]:
            raise ValueError("This is not a valid opcode!")
        return [opcode * (1<<(5*4)) + self.check_5char_hex(number)] #0x100000
    #}}}
    #{{{ and the actual codes
    def Bluebox(self,bluebox_number,x):
        return gen_code(1,x)
    def delay(self,x):
        return [self.gen_code(3,int(round(25.e6*x)))[0] - 100] # give delay in seconds, it converts to clock cycles (2e-3 -> 50000, since 25MHz clock), where the 100 is added in the code, and I have no idea what it is --> it could be from Thomas + incorrect
    def SRAM_start_address(self,x):
        return self.gen_code(8,x)
    def SRAM_stop_address(self,x):
        return self.gen_code(0xa,x)
    def SRAM_range(self,start,length):
        # this sets the range of the SRAM that will be played
        return self.SRAM_start_address(start) + self.SRAM_stop_address(start+length-1)
    #}}}
    
            
    def dacSignal(self,sram,twt_srt = 2e-3, reps=50000, loop=False, getTimingData=False, max_reps = False):
        # total length or sram data
        sramLen = len(sram)
        # memory sequence
        #{{{ Codes
        NoOp = [0x000000]
        start_timer = self.gen_code(4,0)
        stop_timer = self.gen_code(4,1)
        sram_based_timer = self.gen_code(4,2) # documentation says not implemented yet
        play_SRAM = self.gen_code(0xC,0) # he calls this "call SRAM"
        end_of_sequence = self.gen_code(0xF,0) # branch to beginning --> takes two clocks
        #}}}

        # New memory
        memory = NoOp + self.SRAM_range(0,sramLen) + play_SRAM + self.delay(twt_srt) +  end_of_sequence

        # Thomas' Memory List
#        memory = [
#            0x000000, # NoOp
#            0x800000, # SRAM start address
#            0xA00000 + sramLen - 1, # SRAM end address
#            0xC00000, # call SRAM
#            # 0x3186A0, # Delay 4ms to ensure average mode readback completes on A/D
#            0x30C350 - 100, # Delay 2ms (50000 cycles = 2ms since clock is 25 MHz)
#            # Don't know why I need the delay 300 ns shorter, but this gives me an exact 
#            # repetition frequency of 500 Hz.
#            0x400000, # start timer
#            0x400001, # stop timer
#            0xF00000, # branch back to start
#        ]
        # generate maximum number of repetitions that the memory size allows for
        if max_reps:
            for i in range(81):
                memory.insert(5, 0x30C350 - 100)
                memory.insert(5, 0xC00000)
        # send memory and sram to board and run sequence
        self._sendDac(memory,sram,self.fpga)
        if loop:
            while True:
                self.fpga.run_sequence(reps, getTimingData)
        else:
            self.fpga.run_sequence(reps, getTimingData)

    def _sendDac(self,memory, sram, server):
        pack = server.packet()
        pack.select_device(board)
        pack.memory(memory)
        pack.sram(sram)
        pack.send()
        
    
    def synthesize(self,data, loop = True, zero_cal = False, amponly = False, do_normalize = False, trig = [0,1], twt = False,twt_srt = 2e-3,auto_gate = False, max_reps = False,autoGateSwitch = False, shift = False,frontBuffer = 400e-9,rearBuffer = 45.0e-9,longDelay = False,**kwargs):
            
        try: # connect to LabRAD unless connection has already been established 
            self.cxn
        except:
            labrad_connect()

        if do_normalize:
            waveI = data.runcopy(real).data * do_normalize
            waveQ = data.runcopy(imag).data * do_normalize
        else:
            waveI = data.runcopy(real).data
            waveQ = data.runcopy(imag).data

        # Here I will add the lines to shift the waveform it twt = True
        if twt: # This is necessary if we want to compensate for the offset between the pulse and the TWT gate! I can't shift the TWT gate any earlier in time, so I shift the pulse to longer times
            twt_delay = 150 #must be int, in ns, note that TWT gate is still shifted by 16 ns later as well
            tempI = zeros(len(waveI)+twt_delay) #create empty array with proper length
            tempQ = zeros(len(waveQ)+twt_delay)
            tempI[twt_delay::] = waveI #insert waveform at end
            tempQ[twt_delay::] = waveQ
            waveI = tempI #set equal to lengthened array
            waveQ = tempQ

        if zero_cal:
            offset_I = 1*self.zero_cal_data[0]
            offset_Q = 1*self.zero_cal_data[1]
                #self.re_par_inp[1] = self.zero_cal_data[0]
                #self.im_par_inp[1] = self.zero_cal_data[1]
            if twt: #Warning! This is a workaround because the TWT idles at the beginning and I want to include the zero calibration here #You cant have a pulse or gate within the first 
                # I shouldn't need this after I fixed the gate delay issue, but I'm keeping it to be safe because we don't want to gate the TWT for too long if the board idles
                waveI[0:16] = 0
                waveQ[0:16] = 0
            waveI += offset_I
            waveQ += offset_Q
        wave = waveI + 1j*waveQ # put wave back together for hand-off


        if twt and auto_gate:
            twt_gate_array = real(zeros(len(wave)-twt_delay))
            for v, value in enumerate(wave[twt_delay::]):
                if abs(real(value) - offset_I) > 0.001 or abs(imag(value) - offset_Q) > 0.001:
                    print(v)
                    twt_gate_array[v] = 1
            # Go through and find the start of all the pulses
            start_pulse_ix = []
            for i in where(array(twt_gate_array)==1)[0]:
                if twt_gate_array[i-1] == 0:
                    print(i)
                    start_pulse_ix.append(i)
            # Add additional gate to compensate for twt rise time
            for ix in start_pulse_ix:
                twt_gate_array[ix-200:ix] = 1
            twt_gate_array[-100::] = 0 #I think downsampling makes a spike in the pulse at time zero, so here I correct for this by taking the gate away, this should be fine because of the 200ns delay at the beginning of a sequence
            twt_gate_array[0:16] = 0 #board idles at beginning, I don't want to gate the TWT the entire time
#            figure()
#            plot(twt_gate_array)
#            plot(waveI)
#            plot(waveQ)
#            show()
            #check for duty cycle assuming the twt is gated during the entire pulse sequence for safety, change this later!
            duty_cycle = (len(twt_gate_array)*1e-9)/twt_srt
            print('Duty cycle = %e' %duty_cycle)
            if duty_cycle > 100:
                raise ValueError('TWT duty cycle is greater that the allowed 1.5%!!!')


        try:
            sram = self.wave2sram(wave) # convert waveform to SRAM data
        except ValueError:
            if isnan(real(wave)[0]):
                raise ValueError('real part of wave is NaN')
            elif isnan(imag(wave)[0]):
                raise ValueError('imaginary part of wave is NaN')
            else:
                raise ValueError('value error, but neither real nor imaginary part of wave is NaN')

        if autoGateSwitch: # Here add a sequence to the sram that puts out a TTL pulse gate to drive a switch from the j24 and j25 ECL outputs. 
            switchGate = data.copy()
            switchGate.data = abs(switchGate.data)

            # find the bounding values of the pulse
            timeHigh = []
            for count,value in enumerate(switchGate.data):
                if value != 0.0:
                    timeHigh.append(switchGate.getaxis('t')[count])
             
            switchGate['t',:] = 1.0 # clear all data now and make gate 
            timeHigh = array(timeHigh)
            res = 2*abs(switchGate.getaxis('t')[1] - switchGate.getaxis('t')[0])
            jumps = []
            jumps.append(timeHigh.min())
            jumps.append(timeHigh.max())
            for count in range(1,len(timeHigh)): # look at count val and count-1 val
                if abs(timeHigh[count] - timeHigh[count-1]) > res: # we've hit a jump
                    jumps.append(timeHigh[count -1])
                    jumps.append(timeHigh[count])
            jumps.sort()
            bounds = []
            count = 0
            while count < len(jumps):
                bounds.append([jumps[count],jumps[count+1]])
                count += 2
            switchGate['t',:] = 1.0
            for bound in bounds:
                switchGate['t',lambda x: logical_and(x >= bound[0] - frontBuffer, x <= bound[1] + rearBuffer)] = 0.0
            for v, val in enumerate(switchGate.data):
                if val > 0.0:
                    try:
                        sram[v] |= 0x80000000
                    except:
                        print('Didn\'t add trigger at SRAM position %i' %v)
        
        if auto_gate:
            print('Adding gate to SRAM!')
            for v, value in enumerate(twt_gate_array):
                if value > 0:
                    print('Added a gate!!!')
                    try:
                        sram[16+v] |= 0x80000000
                    except:
                        print('Didn\'t add TWT trigger at SRAM position %i' %v)
        elif twt:
            sram = self.add_gate(sram, trig) # add gate for the TWT
        
        if twt:
#            for i in range(16): # Zero pad beginning of sequence. Board idles at beginning.
#                sram[i] = 0 #These two lines were taken out because I want the zero cal to work properly while using the TWT
            sram[16] |= 0x30000000 # add trigger pulse near beginning of sequence
            if loop:
                print 'This is going to hang, but it\'s supposed to...\nIf you don\'t want to be adding a twt delay set twt to False'
            self.dacSignal(sram,twt_srt = twt_srt, loop = loop, max_reps = max_reps)
        elif longDelay:
            sram[16] |= 0x30000000 # add trigger pulse near beginning of sequence
            self.dacSignal(sram,twt_srt = longDelay, loop = False, max_reps = max_reps)
        else:
            sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
            self.fpga.dac_run_sram(sram, loop)



    def wave2sram(self,wave):
        r'''Construct sram sequence for waveform. This takes python array and converts it to sram data for hand off to the FPGA. Wave cannot be nddata - this is stupid...'''
        waveA = real(wave)
        waveB = imag(wave)
        if not len(waveA)==len(waveB):
            raise Exception('Lengths of DAC A and DAC B waveforms must be equal.')
        dataA=[long(floor(0x1FFF*y)) for y in waveA] # Multiply wave by full scale of DAC
        dataB=[long(floor(0x1FFF*y)) for y in waveB]
        truncatedA=[y & 0x3FFF for y in dataA] # Chop off everything except lowest 14 bits
        truncatedB=[y & 0x3FFF for y in dataB]
        dacAData=truncatedA
        dacBData=[y<<14 for y in truncatedB] # Shift DAC B data by 14 bits, why is this done??
        sram=[dacAData[i]|dacBData[i] for i in range(len(dacAData))] # Combine DAC A and DAC B
        return sram

    def add_gate(self,sram, trig):
        # This is the gate for the TWT. Remove this once the trigger channels are programmed.
        if isinstance(trig,tuple): #if a tuple is passed, then it will set multiple triggers for each element of the tuple
            for this_trig in trig:
                for i in range(this_trig[1]+1):
                    sram[16+this_trig[0]+i] |= 0x80000000
        else:
            for i in range(trig[1]+1):
                sram[16+trig[0]+i] |= 0x80000000
        return sram

    def downsample(self,inputdata, bandwidth = 1e9):
        data = inputdata.copy()
        x = data.getaxis('t')
        data.ft('t', shift=True)
        data = data['t',lambda x: abs(x)<5e8] # slice out the center
        f = data.getaxis('t')
        data.data *= exp(-(f**2)/(2.0*((bandwidth/6.)**2))) # multiply by gaussian
        data.ift('t',shift=True)
        return data

