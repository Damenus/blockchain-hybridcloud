#!/usr/bin/python3
import pathlib
import subprocess
import os
import logging
import sys
import socket

import simplejson as simplejson

from hdfssb.common.buffer import *
from hdfssb.client.hdfssb_client import HdfssbClient, json

logging.basicConfig(level=logging.DEBUG)


def download_file(file_name, url_ledger_node):

    # 1. Find where file is

    hdfssb_client = HdfssbClient(base_url=url_ledger_node)

    file_metadata = hdfssb_client.show_file(file_name)
    print("Show file ", file_metadata)

    folder = './thief_file/'
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True)

    # 2. Download

    # PORT = 60002
    # file_size = file_metadata['size']
    #
    # for block_hash, node in file_metadata["blocks_of_file"].items():
    #     print(block_hash + ":" + node)
    #
    #     try:
    #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         s.connect((node, PORT))
    #
    #         with s:
    #             sbuf = Buffer(s)
    #
    #             sbuf.put_utf8(file_metadata["owner"] + "/" + file_metadata["file_name"] + "/" + block_hash)
    #
    #             with open(folder + block_hash, 'wb+') as f:
    #                 remaining = int(file_size) + 4000
    #                 while remaining:
    #                     chunk_size = 4096 if remaining >= 4096 else remaining
    #                     chunk = sbuf.get_bytes(chunk_size)
    #                     if not chunk: break
    #                     f.write(chunk)
    #                     remaining -= len(chunk)
    #                 if remaining:
    #                     print('File incomplete.  Missing', remaining, 'bytes.')
    #                 else:
    #                     print('File received successfully.')
    #             print('Connection closed.')
    #     except Exception as e:
    #         logging.warning("NO node")

    # 2.1

    # for num in [37, 38, 39, 40]:
    #     os.system("scp ddarczuk@100.64.176.{}:/daemon/daemon_dir/  {}".format(num, folder))
    os.system("cp -r /daemon/daemon_dir/ {}".format(folder))

    # 3. Restore raptor file

    mapa = {'checksums': {'sha256': file_metadata['checksums']},
            'data_bytes': int(file_metadata['data_bytes']),
            'oti_common': int(file_metadata['oti_common']),
            'oti_scheme': int(file_metadata['oti_scheme']),
            'symbols': []}

    for filename in os.listdir(folder):
        with open(folder + filename, 'r') as myfile:
            try:
                data = json.load(myfile)
                mapa['symbols'].append(data)
            except:
                logging.error("Not read blopck", filename)

    encoded_file_name = file_name + '.encoded_file'

    with open(encoded_file_name, "w") as twitterDataFile:
        # magic happens here to make it pretty-printed
        twitterDataFile.write(simplejson.dumps(mapa, indent=4, sort_keys=True))

    # 4. Decode file

    decode = """./python-libraptorq/rq \
        --debug \
        decode \
        {path_src} \
        {path_dst}""".format(path_src=encoded_file_name, path_dst=file_name + '.decoded')

    process = subprocess.Popen(decode, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()


if __name__ == "__main__":
    download_file(sys.argv[1], sys.argv[2])
