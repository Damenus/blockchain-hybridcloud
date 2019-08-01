import os
import socket

from hdfssb.client.hdfssb_client import *


cluster_type = key_file = os.getenv('CLUSTER_TYPE', 'public')
key_file = os.getenv('KEY_PATH', 'root.priv')
url_ledger_node = os.getenv('URL_LEDGER_NODE', '127.22.0.1:8008')
name = os.getenv('OWN_IP', socket.gethostname())

hdfssb_client = HdfssbClient(base_url=url_ledger_node, keyfile=key_file)
tx = hdfssb_client.delete_node(name)
print("Deleting node ", tx)
hdfssb_client.wait_for_transaction(tx)
print("Deleted")
