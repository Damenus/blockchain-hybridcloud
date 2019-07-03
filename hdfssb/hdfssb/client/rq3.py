import subprocess
import os
import ast
import hashlib
import json

import socket

import simplejson as simplejson


class Buffer:
    def __init__(self,s):
        '''Buffer a pre-created socket.
        '''
        self.sock = s
        self.buffer = b''

    def get_bytes(self,n):
        '''Read exactly n bytes from the buffered socket.
           Return remaining buffer if <n bytes remain and socket closes.
        '''
        while len(self.buffer) < n:
            data = self.sock.recv(1024)
            if not data:
                data = self.buffer
                self.buffer = b''
                return data
            self.buffer += data
        # split off the message bytes from the buffer.
        data,self.buffer = self.buffer[:n],self.buffer[n:]
        return data

    def put_bytes(self,data):
        self.sock.sendall(data)

    def get_utf8(self):
        '''Read a null-terminated UTF8 data string and decode it.
           Return an empty string if the socket closes before receiving a null.
        '''
        while b'\x00' not in self.buffer:
            data = self.sock.recv(1024)
            if not data:
                return ''
            self.buffer += data
        # split off the string from the buffer.
        data,_,self.buffer = self.buffer.partition(b'\x00')
        return data.decode()

    def put_utf8(self,s):
        if '\x00' in s:
            raise ValueError('string contains delimiter(null)')
        self.sock.sendall(s.encode() + b'\x00')

def main():
    # s = min(file_size - 1, 65528) # 65528 is 2^16 - 8, max uint16_t
    # s = s - s mod 8
    file_name = 'SampleAudio_0.7mb.mp3'
    file_size = os.path.getsize(file_name)
    s = min(file_size - 1, 65528)
    s = s - s % 8

    ###
    # liczba nodów
    # liczba nodów które potrzebne jest
    # drop-rate > repair-symbols-rate
    # private      public       ilosć bloków
    # procent bloków do pirvate
    # (blocks - (blocks*drop_rate)) / nodes > repair-symbols-rate

    # launch your python2 script using bash
    encode = """
    ./python-libraptorq/rq \
    --debug \
    encode \
    -s{s} \
    -m200 \
    --repair-symbols-rate 1 \
    --drop-rate 0.5 \
    {path_src} \
    {path_dst}
    """.format(s=s, path_src=file_name, path_dst=file_name+'.enc')

    decode = """
    ./python-libraptorq/rq \
    --debug \
    decode \
    {path_src} \
    {path_dst}
    """.format(path_src='dd2/enc', path_dst='dd2/dec')
    #""".format(path_src=file_name+'.enc', path_dst=file_name+'.dec')

    process = subprocess.Popen(encode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script

    # "needed: >(\d*),"
    # dla małych plików jak mp3
    # file_encoded_map = os.read_fiel as map

    # with open(file_name+'.enc', 'r') as myfile:
    #     data = myfile.read()
    #
    # mapa = ast.literal_eval(data)

    with open(file_name + '.enc', 'r') as myfile:
        mapa = json.load(myfile)


    user = 'ddarczuk'
    #file_name
    #hash

    i = 0
    for block in mapa['symbols']:
        # hash_object = hashlib.sha1(bytes(block[1]))
        # hex_dig = hash_object.hexdigest()
        # print(hex_dig)

        name = user + '-' + file_name + '-' + str(i)
        i += 1
        # f = open('dd/'+name, "w+")
        # f.write(str(block))
        # f.close()
        with open('dd/'+name, "w+") as json_file:
            json.dump(block, json_file)

    del mapa['symbols']
    # f = open('dd/head', "w+")
    # f.write(str(mapa))
    # f.close()
    with open('dd2/head', "w+") as json_file:
        json.dump(mapa, json_file)


################ Send file
    # for filename in os.listdir('dd'):
    #     # with open('dd/'+filename, 'r') as myfile:
    #     #     data = myfile.read()
    #     with open('dd/' + filename, 'r') as myfile:
    #         data = json.load(myfile)
    #         mapa['symbols'].append(data)
    #


    # hosts = ['127.0.1.1']
    #
    # s = socket.socket()  # Create a socket object
    # host = '127.0.1.1'  # '10.1.1.8' #socket.gethostname()     # Get local machine name
    # port = 60000  # Reserve a port for your service.
    #
    # for filename in os.listdir('dd'):
    #     s.connect((host, port))
    #     s.send((filename+'???').encode())
    #     with open('dd/' + filename, 'rb') as f:
    #         l = f.read(1024)
    #         while (l):
    #             s.send(l)
    #             # print('Sent ', repr(l))
    #             l = f.read(1024)
    #     s.close()

    HOST = socket.gethostname()
    PORT = 60000

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    with s:
        sbuf = Buffer(s)

        # hash_type = input('Enter hash type: ')
        #
        # files = input('Enter file(s) to send: ')
        # files_to_send = files.split()

        for file_name in os.listdir('dd'):
            print(file_name)
            # sbuf.put_utf8(hash_type)
            sbuf.put_utf8(file_name)

            file_size = os.path.getsize('dd/'+file_name)
            sbuf.put_utf8(str(file_size))

            with open('dd/'+file_name, 'rb') as f:
                sbuf.put_bytes(f.read())
            print('File Sent')

################# Recive file


    PORT = 60002

    for file_name in os.listdir('dd'):
        print(file_name)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        with s:
            sbuf = Buffer(s)


            # sbuf.put_utf8(hash_type)
            sbuf.put_utf8(file_name)

            with open('./dd3/'+file_name, 'wb+') as f:
                remaining = file_size
                while remaining:
                    chunk_size = 4096 if remaining >= 4096 else remaining
                    chunk = sbuf.get_bytes(chunk_size)
                    if not chunk: break
                    f.write(chunk)
                    remaining -= len(chunk)
                if remaining:
                    print('File incomplete.  Missing', remaining, 'bytes.')
                else:
                    print('File received successfully.')
            print('Connection closed.')


###############



    # with open('dd/head', 'r') as myfile:
    #     data = myfile.read()
    #
    # mapa = ast.literal_eval(data)
    with open('dd2/head', 'r') as myfile:
        mapa = json.load(myfile)

    mapa['symbols'] = []
    print(mapa)

    for filename in os.listdir('dd'):
        # with open('dd/'+filename, 'r') as myfile:
        #     data = myfile.read()
        with open('dd/'+filename, 'r') as myfile:
            data = json.load(myfile)
            mapa['symbols'].append(data)

    # f = open('dd/enc', "w+")
    # f.write(str(mapa))
    # f.close()
    with open('dd2/enc', "w+") as json_file:
        json.dump(mapa, json_file)

    # now write output to a file
    twitterDataFile = open("dd2/enc2", "w")
    # magic happens here to make it pretty-printed
    twitterDataFile.write(simplejson.dumps(mapa, indent=4, sort_keys=True))
    twitterDataFile.close()

    process = subprocess.Popen(decode.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()  # receive output from the python2 script


if __name__ == "__main__":
    main()
