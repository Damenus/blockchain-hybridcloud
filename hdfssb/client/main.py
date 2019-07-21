import socket

s = socket.socket()             # Create a socket object
host = '127.0.1.1' #'10.1.1.8' #
host = socket.gethostname()     # Get local machine name
port = 60000                    # Reserve a port for your service.

s.connect((host, port))
s.send(b"Hello server!")

filename = 'mytext.txt'
f = open(filename, 'rb')
l = f.read(1024)
while (l):
    s.send(l)
    print('Sent ', repr(l))
    l = f.read(1024)

f.close()
s.close()
