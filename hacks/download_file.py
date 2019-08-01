import argparse
import pathlib
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


def download_file(file_name, user, url_ledger_node, key_file):

    # 1. Find where file is

    hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)

    file_metadata = hdfssb_client.show_file(file_name)
    print("Show file ", file_metadata)

    folder = './thief_file/'

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