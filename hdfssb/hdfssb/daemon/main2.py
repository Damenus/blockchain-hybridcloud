import socket
import logging
import os

from hdfssb.hdfssb.common.buffer import Buffer


logging.basicConfig(level=logging.DEBUG)

DIR = "/daemon/daemon_dir/"
DIR = "./daemon/"

port = 60002  # Reserve a port for your service.
s = socket.socket()  # Create a socket object
host = socket.gethostname()  # Get local machine name
s.bind((host, port))  # Bind to the port
s.listen(5)  # Now wait for client connection.

logging.debug('Server listening....')

while True:
    conn, addr = s.accept()
    print("Got a connection from ", addr)
    connbuf = Buffer(conn)

    file_name = connbuf.get_utf8()
    if not file_name:
        break
    file_name = os.path.join(DIR,file_name)
    print('file name: ', file_name)

    with open(file_name, 'rb') as f:
        connbuf.put_bytes(f.read())
    print('File Sent')

    print('Connection closed.')
    conn.close()
