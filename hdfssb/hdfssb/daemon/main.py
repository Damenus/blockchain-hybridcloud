import socket
import logging

logging.basicConfig(level=logging.DEBUG)

DIR = "/daemon/daemon_dir/"

port = 60000  # Reserve a port for your service.
s = socket.socket()  # Create a socket object
host = socket.gethostname()  # Get local machine name
s.bind((host, port))  # Bind to the port
s.listen(5)  # Now wait for client connection.

logging.debug('Server listening....')

while True:
    conn, addr = s.accept()  # Establish connection with client.
    logging.debug('Got connection from', addr)
    data = conn.recv(1024)
    logging.debug('Server received', repr(data))

    with open(DIR + 'dd', 'wb+') as f:
        f.write(data)
        while True:
            data = conn.recv(1024)
            logging.debug('data=%s', (data))
            if not data:
                break
            f.write(data)

    conn.close()
