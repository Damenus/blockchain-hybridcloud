print('Registring...')
dd = HdfssbClient(base_url='127.22.0.1:8008', keyfile='key.priv')


file_to_send = dict(file_name="file1", owner="dd",
                    state="dd ", size="dd", file_hash="dd",
                    blocks_of_file={"adsasd": "10.0.0.1", "asdasdas": "10.0.0.2"}, checksums="dd", data_bytes="dd",
                    oti_common="dd", oti_scheme="dd", last_update=str(time.time()))
print(file_to_send)
tx = dd.add_file(name="file1", payload_object=file_to_send)
print("Add file ", tx)
dd.wait_for_transaction(tx)
print("Files ", dd.list_files())

print("Show file ", dd.show_file("file1"))

# new_node = dict(node_name="node1", capacity=123, taken_space=0, reversed_space=0, last_update=str(time.time()))
#
# print(new_node)
# print("Add node ", dd.add_node(name="node1", payload_object=new_node))
#
# print("Nodes ", dd.list_nodes())

exit(0)
