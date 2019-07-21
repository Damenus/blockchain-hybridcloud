import pathlib
import subprocess
import os
import logging
import socket

import simplejson as simplejson

from hdfssb.common.buffer import *
from hdfssb.common.hash import sha1_file

logging.basicConfig(level=logging.DEBUG)


def main():
    send_file()
    download_file()


def send_file():
    key_file = 'key.priv'
    url_ledger_node = '127.22.0.1:8008'
    user = 'ddarczuk'
    file_name = 'SampleAudio_0.7mb.mp3'
    HOST = socket.gethostname()
    PORT = 60000

    owner_folder = './tmp_send/' + user + '/'
    folder = owner_folder + file_name + '/'
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

    # 1. Encode file by raptor

    # s = min(file_size - 1, 65528) # 65528 is 2^16 - 8, max uint16_t
    # s = s - s mod 8
    file_size = os.path.getsize(file_name)
    s = min(file_size - 1, 65528)
    s = s - (s % 8)

    ###
    # liczba nodów
    # liczba nodów które potrzebne jest
    # drop-rate > repair-symbols-rate
    # private      public       ilosć bloków
    # procent bloków do pirvate
    # (blocks - (blocks*drop_rate)) / nodes > repair-symbols-rate

    #  ./python-libraptorq/rq --debug encode -s1600 -m200 --repair-symbols-rate 1 --drop-rate 0.5 README.rst README.rst.enc

    # launch your python2 script using bash
    encode = """./python-libraptorq/rq \
    --debug \
    encode \
    -s{s} \
    -m200 \
    --repair-symbols-rate 1 \
    {path_src} \
    {path_dst}""".format(s=s, path_src=file_name, path_dst=owner_folder + file_name+'.enc') #.split("\n")  # --drop-rate 0.5 \

    process = subprocess.Popen(encode, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()  # receive output from the python2 script

    # "needed: >(\d*),"
    # dla małych plików jak mp3
    # file_encoded_map = os.read_fiel as map

    # 2. Load encoded file and split blocks to files

    with open(owner_folder + file_name+'.enc', 'r') as myfile:
        mapa = json.load(myfile)

    for block in mapa['symbols']:
        block_string = json.dumps(block)
        hash_name = hashlib.sha1(str.encode(block_string)).hexdigest()
        with open(folder + hash_name, "w+") as file:
            file.write(block_string)
        logging.info("Create block ", block_string)

    del mapa['symbols']
    logging.info("MAPA: ", mapa)

    # 3. Read ledger, to find nodes where send blocks

    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)

    nodes = hdfssb_client.list_nodes()
    logging.info("Nodes ", nodes)

    valid_nodes = []
    for node in nodes:
        node = node.decode().split(",")
        #if node[] # dodaj jeśli jest wolne miejsce na nodzie i dodaj procent private i publick
        valid_nodes.append(node[0])

    # 4. Assign blocks to nodes

    dict_block_to_node = {}
    length = len(valid_nodes)
    i = 0
    files_names = os.listdir(folder)

    for block in files_names:
        dict_block_to_node[block] = valid_nodes[i]
        i += 1
        if i == length:
            i = 0

    # 5. Save information in ledger

    file_to_send = dict(file_name=file_name,
                        owner=user,
                        state="requested",
                        size=file_size,
                        file_hash=sha1_file(file_name),
                        blocks_of_file=dict_block_to_node,
                        checksums=mapa['checksums']['sha256'],
                        data_bytes=mapa['data_bytes'],
                        oti_common=mapa['oti_common'],
                        oti_scheme=mapa['oti_scheme'],
                        last_update=str(time.time()))
    logging.info(file_to_send)
    tx = hdfssb_client.add_file(name=file_name, payload_object=file_to_send)
    logging.info("Add file ", tx)
    hdfssb_client.wait_for_transaction(tx)

    # 6. Send file
    # for block, node in os.listdir(folder):
    for block, node in dict_block_to_node.items():

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((node, PORT))

        with s:
            sbuf = Buffer(s)

            print(block)

            sbuf.put_utf8(file_name)

            file_size = os.path.getsize(folder + block)
            sbuf.put_utf8(str(file_size))

            with open(folder + block, 'rb') as f:
                sbuf.put_bytes(f.read())
            print('File Sent')


def download_file():
    HOST = socket.gethostname()
    PORT = 60002
    file_name = 'SampleAudio_0.7mb.mp3'
    key_file = 'key.priv'
    url_ledger_node = '127.22.0.1:8008'

    # 1. Find where file is

    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)

    file_metadata = hdfssb_client.show_file(file_name)
    print("Show file ", file_metadata)

    file_size = file_metadata['size']

    # 2. For each block, connect to node and download

    owner_folder = './tmp_download/' + file_metadata['owner'] + '/'
    folder = owner_folder + file_metadata['file_name'] + '/'
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

    for block_hash, node in file_metadata["blocks_of_file"].items():
        print(block_hash + ":" + node)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))

        with s:
            sbuf = Buffer(s)

            sbuf.put_utf8(file_metadata["owner"] + "/" + file_metadata["file_name"] + "/" + block_hash)

            with open(folder + block_hash, 'wb+') as f:
                remaining = int(file_size) + 4000
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


    # 3. Restore raptor file

    mapa = {'checksums': {'sha256': file_metadata['checksums']},
            'data_bytes': int(file_metadata['data_bytes']),
            'oti_common': int(file_metadata['oti_common']),
            'oti_scheme': int(file_metadata['oti_scheme']),
            'symbols': []}

    time.sleep(3)

    for filename in os.listdir(folder):
        with open(folder + filename, 'r') as myfile:
            data = json.load(myfile)
            mapa['symbols'].append(data)

    # with open(owner_folder + 'enc', "w+") as json_file:
    #     json.dump(mapa, json_file)

    encoded_file_name = owner_folder + file_name + '.encoded_file'

    with open(encoded_file_name, "w") as twitterDataFile:
        # magic happens here to make it pretty-printed
        twitterDataFile.write(simplejson.dumps(mapa, indent=4, sort_keys=True))

    # 4. Decode file

    decode = """./python-libraptorq/rq \
        --debug \
        decode \
        {path_src} \
        {path_dst}""".format(path_src=encoded_file_name, path_dst=owner_folder + file_name + '.decoded')

    process = subprocess.Popen(decode, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()  # receive output from the python2 script


if __name__ == "__main__":
    main()