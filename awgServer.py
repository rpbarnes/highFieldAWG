import socket
import synthesize as s
from pylab import *
ion()
import time

try:
	p
except:
	p = s.pulsegen()

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
sock.bind(('128.111.114.94',9000)) 
### Outside facing ip is 128.111.114.94
sock.listen(5)
print "Server is live"
while True:
    conn,addr = sock.accept()
    time.sleep(1.0)
    close('all')
    print 'Got connection from ', addr
    incoming = ''
    command_buffer = []
    try: # if this faults out lets remake the connection with the host machine
        temp = conn.recv(16384000) 
        print temp
        print 'length of temp:'
        print len(temp.split(','))
    except:
        conn.close()
        conn, addr = sock.accept()
        temp = conn.recv(128) # if nothing received the script hangs

    if not temp:
        print "I did not recieve anything"
        pass
    else:
        incoming = incoming + temp
        if incoming[-1] != '\n':
            if incoming.find('\n'):
                temp = incoming.split('\\n')
                command_buffer.extend(temp[:-1])
                incoming = temp[-1]
            else:
                print "waiting for new line character"
                pass
        else:
            command_buffer.extend(incoming.split('\n'))
            incoming = 'none'
        print 'command buffer'    
        print command_buffer
        print 'end command buffer'
        # parse out the command buffer.
        #if command_buffer[0].find('real:'):
        # this is a waveform
        print 'incoming:'
        print incoming
        print 'end incoming'

        real = command_buffer[0].split('real:')[1].split('imag:')[0].split(',')
        real.pop(-1)
        real = array([float(k) for k in real])
        imag = command_buffer[0].split('imag:')[1].split(',')
        imag.pop(-1)
        imag = array([float(k) for k in imag])
        print real
        print imag
        figure()
        plot(real)
        plot(imag)
        draw()
        sram = p.wave2sram(real+1j*imag)
        sram[0] |= 0x30000000 # add trigger pulse at beginning of sequence
        p.fpga.dac_run_sram_slave(sram,False)
        print "synthesized waveform"

    conn.send('Thank you for connecting')
    conn.close()
    del conn

