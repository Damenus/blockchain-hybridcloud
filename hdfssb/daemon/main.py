import socket
import logging
import os

import pathlib

import time

from shutil import copyfile

from hdfssb.common.buffer import *
from hdfssb.common.hash import *
from hdfssb.client.hdfssb_client import *

def _sha512(data):
    return hashlib.sha512(data).hexdigest()


class XoException(Exception):
    pass


FAMILY_NAME = 'hdfssb'

cluster_type = key_file = os.getenv('CLUSTER_TYPE', 'public')
key_file = os.getenv('KEY_PATH', 'root.priv')
url_ledger_node = os.getenv('URL_LEDGER_NODE', '127.22.0.1:8008')
name = os.getenv('OWN_IP', socket.gethostname())  # "node5"
#name = name + '.hdfssb-daemon'
taken_space = 0

logging.basicConfig(level=logging.DEBUG)

print('Registring...')
hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)
new_node = dict(node_name=name, cluster=cluster_type, capacity=1000, taken_space=taken_space, reversed_space=0, last_update=str(time.time()))
print(new_node)
tx = hdfssb_client.add_node(name=name, payload_object=new_node)
print("Add node ", tx)
hdfssb_client.wait_for_transaction(tx)

DIR = "/daemon/daemon_dir/"
# DIR = "./daemon/"

port = 60000  # Reserve a port for your service.
s = socket.socket()  # Create a socket object
#host = socket.gethostname()  # Get local machine name
s.bind((name, port))  # Bind to the port
s.listen(5)  # Now wait for client connection.

logging.debug('Server listening....')

while True:
    conn, addr = s.accept()
    print("Got a connection from ", addr)
    connbuf = Buffer(conn)

    while True:
        file_name = connbuf.get_utf8()
        if not file_name:
            break
        temp_file_name = os.path.join(DIR,"tmp")
        print('file name: ', file_name)

        file_size = int(connbuf.get_utf8())
        print('file size: ', file_size )

        file = hdfssb_client.show_file(file_name)
        print("FILE block: ", file)

        sha1 = hashlib.sha1()

        with open(temp_file_name, 'wb+') as f:
            remaining = file_size
            while remaining:
                chunk_size = 4096 if remaining >= 4096 else remaining
                chunk = connbuf.get_bytes(chunk_size)
                if not chunk: break
                f.write(chunk)
                sha1.update(chunk)
                remaining -= len(chunk)
            if remaining:
                print('File incomplete.  Missing',remaining,'bytes.')
            else:
                print('File received successfully.')

        file_hash = sha1_file(temp_file_name)  # sha1.hexdigest()
        print("SHA1: {0}".format(file_hash))

        # Check downloaded file if exist in blockchain, next delete or confirm na blockchain
        ### test hash recived file

        if file_hash in file["blocks_of_file"].keys():
            # copy file_name to file["owner"]/"name"/hash
            pathlib.Path(DIR + file["owner"] + "/" + file["file_name"]).mkdir(parents=True, exist_ok=True)
            copyfile(temp_file_name, DIR + file["owner"] + "/" + file["file_name"] + "/" + file_hash)
        else:
            # delete file_name
            os.remove(temp_file_name)

        # update blockchain that less space on node
        # tx = hdfssb_client.update_node(name=name, taken_space=taken_space)
        # print("Add node ", tx)
        # hdfssb_client.wait_for_transaction(tx)

        # update blockchain that part file is on node

    print('Connection closed.')
    conn.close()


# while True:
#     conn, addr = s.accept()  # Establish connection with client.
#     # logging.debug('Got connection from', addr)
#     logging.debug('Got connection')
#     data = conn.recv(1024).decode()
#     name = data.split('???', 1)[0]
#     data = data.split('???', 1)[1]
#     logging.debug('Server received', name)
#
#     with open(DIR + name, 'wb+') as f:
#         f.write(data)
#         while True:
#             data = conn.recv(1024)
#             logging.debug('data=%s', (data))
#             if not data:
#                 break
#             f.write(data)
#
#     conn.close()
