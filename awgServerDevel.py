import socket
import time
from astropy.io import ascii
from astropy.table import Table,Column
import synthesize as s
from pylab import *
import time
ion()

makePlots = True
phaseScaling = False    # set to False to prevent scaling the phase of waveform by 1/16.
dwellTime = 1e-9        # set to the dwell time of the FPGA. Must be a multiple of 4 ns.
localDebug = False      # binds server to local host. False = bound to outside accessible ip. True = bound to localhost.
dryRun = False          # for debug purposes. Set to False to synthesize waveform. If set to True script will run everything but final waveform synthesis.
saveWaveforms = False 	# if true this will save the waveform recieved from specman in the folder 'savedWaveforms'
reprogrammingDelay = False # set to True if you want to hang for the 150 ms reprogramming delay
reprogrammingTime = 5. # time to reprogram the DAC board.


def recvTimeout(Sconn,timeout=1.,verbose=False):
    Sconn.setblocking(0) # make it so the socket doesn't block
    # put the data together peicewise 
    totalData=[]
    data=''
    startTime = time.time()
    while 1:
        # if you have some data then break
        if totalData and time.time()-startTime>timeout:
            break
        # if you have no data wait a little longer.
        elif time.time()-startTime > timeout*2:
            break
        # recv the data 
        try:
            data = Sconn.recv(4096)
            if data:
                totalData.append(data)
                startTime = time.time() # reset the counter
                if verbose:
                    print "recieved new packet"
            else:
                pass
        except:
            pass
    # return a string of the data
    return ''.join(totalData)

def makeWaveform(incomingString,phaseScaling=True):
    """ Produce a waveform with modifiers from incoming string recieved by server
        
        args:
        incomingString - str - string recieved by specman Client.
        phaseScaling - boolean - True scales phase by 1./16. False leaves phase as is.

        returns:
        wave - complex array - array to send to dac board.
    """
    re = incomingString.split('real:')[1].split('imag:')[0].split(',')
    re.pop(-1)
    re = array([float(k) for k in re])
    im = incomingString.split('imag:')[1].split(',')
    im.pop(-1)
    im = array([float(k) for k in im])
    wave = re+1j*im
    if phaseScaling:
        phase = unwrap(arctan2(im,re))
        phase /= 16.
        newWave = abs(wave)*exp(1j*phase) # normalize by the appropriate amplitude.
	newWave /= newWave.max()
    else:
        newWave = None 
    return wave,newWave


try:
	p
except:
	p = s.pulsegen()

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
if localDebug:
    sock.bind(('127.0.0.1',9000)) 
else:
    sock.bind(('128.111.114.94',9000)) 
### Outside facing ip is 128.111.114.94
sock.listen(1)
print "Server is live"
while True:
    conn,addr = sock.accept()
    close('all')
    print 'Got connection from ', addr
    incoming = recvTimeout(conn,verbose=True)
    print "the length of the waveform recieved is ",len(incoming)
    if len(incoming) > 0:
        wave,newWave = makeWaveform(incoming,phaseScaling=phaseScaling)
        timeAxis = arange(0,len(wave)*dwellTime,dwellTime)
        if makePlots:
            close('all')
            figure()
            plot(timeAxis,real(wave),label='real')
            plot(timeAxis,imag(wave),label='imag')
            plot(timeAxis,abs(wave),label='abs')
            legend()
            title('Original Waveform')
            draw()
            if phaseScaling:
                figure()
                plot(timeAxis,real(newWave),label='real')
                plot(timeAxis,imag(newWave),label='imag')
                plot(timeAxis,abs(newWave),label='abs')
                legend()
                title('Phase Scaled Waveform')
                draw()
        # synthesize the waveform
        try:
            # I'm really not sure if this is the right thing to do but for some reason the imag channel is getting flipped.
            wave = real(wave)-1j*imag(wave)
            if phaseScaling:
                sram = p.wave2sram(newWave)
            else:
                sram = p.wave2sram(wave)
            sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
            if not dryRun:
                p.fpga.dac_run_sram_slave(sram,False)
                #p.fpga.dac_run_sram(sram,False)
            else:
                print "Dry Run. Did not send wave to DAC "
            print "synthesized waveform"
            if saveWaveforms:
                fileName = 'savedWaveforms/'+str(time.strftime("%Y-%m-%d_%H-%M"))+'.dat'
                if phaseScaling:
                    dataWriter = Table([real(newWave),imag(newWave)],names=['real','imag'])
                else:
                    dataWriter = Table([real(wave),imag(wave)],names=['real','imag'])
                ascii.write(dataWriter,fileName)
            if reprogrammingDelay:
                print "Sleeping for %0.3f s for reprogramming the DAC"%reprogrammingTime
                time.sleep(reprogrammingTime) # sleep for 150 ms.
            conn.send('Waveform Synthesized')
        except Exception as errtxt:
            print errtxt
            conn.send('Trouble Synthesizing waveform! Restart DAC connection on computer!')

    else:
        conn.send('Did not receive any data.')
    conn.close()

