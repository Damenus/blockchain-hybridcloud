import argparse
import pathlib
import re
import subprocess
import os
import logging
import socket
import json

import simplejson as simplejson

from hdfssb.common.buffer import *
from hdfssb.common.hash import sha1_file
from hdfssb.client.hdfssb_client import *

logging.basicConfig(level=logging.DEBUG)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='command', help="Command: send or download")
    parser.add_argument(dest='file_name')
    # parser.add_argument(dest='user')
    parser.add_argument(dest='url_ledger_node')
    parser.add_argument(dest='key_file')

    args = parser.parse_args()

    if args.command == 'send':
        send_file(args.file_name, args.url_ledger_node, args.key_file)
    elif args.command == 'download':
        download_file(args.file_name, args.url_ledger_node, args.key_file)
    elif args.command == 'list_files':
        list_files(args.url_ledger_node, args.key_file)
    elif args.command == 'list_nodes':
        list_nodes(args.url_ledger_node, args.key_file)

# export PYTHONPATH=../.. ; python3 rq3.py send SampleAudio_0.7mb.mp3 ddarczuk 192.168.0.150:31454 /project/keys/root.priv
# export PYTHONPATH=../.. ; python3 rq3.py download SampleAudio_0.7mb.mp3 ddarczuk 192.168.0.150:31454 /project/keys/root.priv
# export PYTHONPATH=../.. ; python3 rq3.py send SampleAudio_0.7mb.mp3 ddarczuk 192.168.0.150:8008 /project/keys/root.priv
# export PYTHONPATH=../.. ; python3 rq3.py download SampleAudio_0.7mb.mp3 ddarczuk 192.168.0.150:31454 /project/keys/root.priv


def list_files(url_ledger_node, key_file):
    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)
    print(hdfssb_client.list_files_decoded())


def list_nodes(url_ledger_node, key_file):
    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)
    print(hdfssb_client.list_nodes_decoded())


def send_file(file_name, url_ledger_node, key_file):
    #key_file = 'root.priv'
    #url_ledger_node = '127.22.0.1:8008'
    #user = 'ddarczuk'
    #file_name = 'SampleAudio_0.7mb.mp3'
    HOST = socket.gethostname()
    PORT = 60000

    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)
    public_key = hdfssb_client.get_public_key()
    user = public_key

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
    encode = """./hdfssb/client/python-libraptorq/rq \
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

    x = re.search(r'(?P<symbols>\d*) symbols \(needed: >(?P<needed>\d*)', output.decode("utf-8"))
    needed = int(x['needed'])
    symbols = int(x['symbols'])
    # 2. Load encoded file and split blocks to files

    with open(owner_folder + file_name+'.enc', 'r') as myfile:
        mapa = json.load(myfile)

    for block in mapa['symbols']:
        block_string = json.dumps(block)
        hash_name = hashlib.sha1(str.encode(block_string)).hexdigest()
        with open(folder + hash_name, "w+") as file:
            file.write(block_string)
        # logging.info("Create block ", block_string)

    del mapa['symbols']
    logging.info("MAPA: ", mapa)

    # 3. Read ledger, to find nodes where send blocks

    nodes = hdfssb_client.list_nodes_decoded()
    logging.info("Nodes ", nodes)

    needed = int(x['needed'])
    symbols = int(x['symbols'])

    max_number_public_node = needed - 1
    max_number_private_node = symbols - needed + 1

    valid_nodes = []
    number_private_node = 0
    number_public_node = 0

    for node_name, dict_atribute in nodes.items():
        #node = node.decode().split(",")
        #if node[] # dodaj jesli jest wolne miejsce na nodzie i dodaj procent private i publick
        #valid_nodes.append(node[0])

        if dict_atribute['capacity'] < dict_atribute['taken_space'] + dict_atribute['reversed_space']:
            continue

        if dict_atribute['cluster'] == 'private' and number_private_node <= max_number_private_node:
            number_private_node += 1
            valid_nodes.append(node_name)
        elif dict_atribute['cluster'] == 'public' and number_public_node <= max_number_public_node:
            number_public_node += 1
            valid_nodes.append(node_name)


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

        try:
            # exception if not name know socket.gaierror: [Errno -2] Name or service not known
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
        except Exception as e:
            logging.warning("NO node")


def download_file(file_name, url_ledger_node, key_file):
    HOST = socket.gethostname()
    PORT = 60002
    #file_name = 'SampleAudio_0.7mb.mp3'
    #key_file = 'root.priv'
    #url_ledger_node = '127.22.0.1:8008'

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

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((node, PORT))

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
        except Exception as e:
            logging.warning("NO node")

    # 3. Restore raptor file

    mapa = {'checksums': {'sha256': file_metadata['checksums']},
            'data_bytes': int(file_metadata['data_bytes']),
            'oti_common': int(file_metadata['oti_common']),
            'oti_scheme': int(file_metadata['oti_scheme']),
            'symbols': []}

    time.sleep(5)

    for filename in os.listdir(folder):
        with open(folder + filename, 'r') as myfile:
            try:
                data = json.load(myfile)
                mapa['symbols'].append(data)
            except:
                logging.error("Not read blopck", filename)

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
