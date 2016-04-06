import socket

sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
serverAddress = ('127.0.0.1',9000) # address to the xepr computer
#serverAddress = ('localhost',7000) # address to the xepr computer
sock.connect(serverAddress)
sock.send('This is a command\n')
print sock.recv(128)
sock.close()

