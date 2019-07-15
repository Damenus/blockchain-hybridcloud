import socket
import logging
import os

import hashlib
import base64
from base64 import b64encode
import time
import random
import requests
import yaml

import hashlib
import base64
import random
import requests
import yaml
import json

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch

from hdfssb.hdfssb.client.hdfssb_client import *
from hdfssb.hdfssb.common.buffer import *

def _sha512(data):
    return hashlib.sha512(data).hexdigest()


class XoException(Exception):
    pass


# class Buffer:
#     def __init__(self,s):
#         '''Buffer a pre-created socket.
#         '''
#         self.sock = s
#         self.buffer = b''
#
#     def get_bytes(self,n):
#         '''Read exactly n bytes from the buffered socket.
#            Return remaining buffer if <n bytes remain and socket closes.
#         '''
#         while len(self.buffer) < n:
#             data = self.sock.recv(1024)
#             if not data:
#                 data = self.buffer
#                 self.buffer = b''
#                 return data
#             self.buffer += data
#         # split off the message bytes from the buffer.
#         data,self.buffer = self.buffer[:n],self.buffer[n:]
#         return data
#
#     def put_bytes(self,data):
#         self.sock.sendall(data)
#
#     def get_utf8(self):
#         '''Read a null-terminated UTF8 data string and decode it.
#            Return an empty string if the socket closes before receiving a null.
#         '''
#         while b'\x00' not in self.buffer:
#             data = self.sock.recv(1024)
#             if not data:
#                 return ''
#             self.buffer += data
#         # split off the string from the buffer.
#         data,_,self.buffer = self.buffer.partition(b'\x00')
#         return data.decode()
#
#     def put_utf8(self,s):
#         if '\x00' in s:
#             raise ValueError('string contains delimiter(null)')
#         self.sock.sendall(s.encode() + b'\x00')


FAMILY_NAME = 'hdfssb'


def _hash(data):
    return hashlib.sha512(data).hexdigest()

logging.basicConfig(level=logging.DEBUG)

print('Registring...')
name = "node5"
dd = HdfssbClient(base_url='127.22.0.1:8008', keyfile='key.priv')
new_node = dict(node_name=name, capacity=123, taken_space=0, reversed_space=0, last_update=str(time.time()))
print(new_node)
asd = dd.add_node(name=name, payload_object=new_node)
print("Add node ", asd)
dd.wait_for_transaction(asd)
print("Nodes ", dd.list_nodes())

DIR = "/daemon/daemon_dir/"
DIR = "./daemon/"

port = 60000  # Reserve a port for your service.
s = socket.socket()  # Create a socket object
host = socket.gethostname()  # Get local machine name
s.bind((host, port))  # Bind to the port
s.listen(5)  # Now wait for client connection.

logging.debug('Server listening....')

while True:
    conn, addr = s.accept()
    print("Got a connection from ", addr)
    connbuf = Buffer(conn)

    while True:
        # hash_type = connbuf.get_utf8()
        # if not hash_type:
        #     break
        # print('hash type: ', hash_type)

        file_name = connbuf.get_utf8()
        if not file_name:
            break
        file_name = os.path.join(DIR,file_name)
        print('file name: ', file_name)

        file_size = int(connbuf.get_utf8())
        print('file size: ', file_size )

        with open(file_name, 'wb+') as f:
            remaining = file_size
            while remaining:
                chunk_size = 4096 if remaining >= 4096 else remaining
                chunk = connbuf.get_bytes(chunk_size)
                if not chunk: break
                f.write(chunk)
                remaining -= len(chunk)
            if remaining:
                print('File incomplete.  Missing',remaining,'bytes.')
            else:
                print('File received successfully.')

        # Check downloaded file if exist in blockchain, next delete or confirm na blockchain

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
