from base64 import b64encode
import time

import base64
import random
import requests
import yaml

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch

from hdfssb.processor.file import *


FAMILY_NAME = 'hdfssb'


def _sha512(data):
    return hashlib.sha512(data).hexdigest()


def _hash(data):
    return hashlib.sha512(data).hexdigest()


class XoException(Exception):
    pass


class HdfssbClient:
    def __init__(self, base_url, keyfile=None):

        self._base_url = base_url

        if keyfile is None:
            self._signer = None
            return

        try:
            with open(keyfile) as fd:
                private_key_str = fd.read().strip()
        except OSError as err:
            raise XoException(
                'Failed to read private key {}: {}'.format(
                    keyfile, str(err)))

        try:
            private_key = Secp256k1PrivateKey.from_hex(private_key_str)
        except ParseError as e:
            raise XoException(
                'Unable to load private key: {}'.format(str(e)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(private_key)

        self._publicKey = self._signer.get_public_key().as_hex()

        self._address_file = _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
                        _hash(self._publicKey.encode('utf-8'))[0:64]

    def _get_prefix(self):
        return _sha512('hdfssb'.encode('utf-8'))[0:6]

    def _get_prefix_file(self):
        return _sha512('file'.encode('utf-8'))[0:4]

    def _get_prefix_node(self):
        return _sha512('node'.encode('utf-8'))[0:4]

    def _get_address_file(self, name):
        hdfssb_prefix = self._get_prefix()
        file_prefix = self._get_prefix_file()
        name_hash = _sha512(name.encode('utf-8'))[0:60]
        return hdfssb_prefix + file_prefix + name_hash

    def _get_address_node(self, name):
        hdfssb_prefix = self._get_prefix()
        node_prefix = self._get_prefix_node()
        name_hash = _sha512(name.encode('utf-8'))[0:60]
        return hdfssb_prefix + node_prefix + name_hash

    def add_file(self, name, payload_object, wait=None, auth_user=None, auth_password=None):
        return self._send_xo_txn(
            name=name,
            address=self._get_address_file(name),
            payload_object=payload_object,
            action="add_file",
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def delete_file(self, name, wait=None, auth_user=None, auth_password=None):
        return self._send_xo_txn(
            name,
            None,
            "delete_file",
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def add_node(self, name, payload_object, wait=None, auth_user=None, auth_password=None):
        return self._send_xo_txn(
            name=name,
            address=self._get_address_node(name),
            payload_object=payload_object,
            action="add_node",
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def delete_node(self, name, wait=None, auth_user=None, auth_password=None):
        return self._send_xo_txn(
            name,
            None,
            "delete_node",
            wait=wait,
            auth_user=auth_user,
            auth_password=auth_password)

    def list_files(self, auth_user=None, auth_password=None):
        hdfssb_prefix = self._get_prefix()
        file_prefix = self._get_prefix_file()

        result = self._send_request(
            "state?address={}".format(hdfssb_prefix + file_prefix),
            auth_user=auth_user,
            auth_password=auth_password)

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                base64.b64decode(entry["data"]) for entry in encoded_entries
            ]

        except BaseException:
            return None

    def list_files_decoded(self):
        list_files = self.list_files()

        nodes = {}
        try:
            for node in list_files:
                file_name, owner, state, state, size, file_hash, blocks_str, checksums, data_bytes, oti_common, oti_scheme, last_update = node.decode().split(",")
                blocks = blocks_str.split("+")
                blocks_of_file = {}
                for pair in blocks:
                    block, node = pair.split(":")
                    blocks_of_file[block] = node

                nodes[file_name] = [file_name, owner, state, size, file_hash, blocks_of_file, checksums, data_bytes, oti_common, oti_scheme, last_update]
        except ValueError:
            raise InternalError("Failed to deserialize game data")

        return nodes

    def list_nodes(self, auth_user=None, auth_password=None):
        hdfssb_prefix = self._get_prefix()
        node_prefix = self._get_prefix_node()

        result = self._send_request(
            "state?address={}".format(hdfssb_prefix + node_prefix),
            auth_user=auth_user,
            auth_password=auth_password)

        try:
            encoded_entries = yaml.safe_load(result)["data"]

            return [
                base64.b64decode(entry["data"]) for entry in encoded_entries
            ]

        except BaseException:
            return None

    def show_file(self, name, auth_user=None, auth_password=None):
        address = self._get_address_file(name)

        result = self._send_request(
            "state/{}".format(address),
            name=name,
            auth_user=auth_user,
            auth_password=auth_password)
        try:
            file = base64.b64decode(yaml.safe_load(result)["data"])

            file_name, owner, state, state, size, file_hash, blocks_str, checksums, data_bytes, oti_common, oti_scheme, last_update = file.decode().split(",")
            blocks = blocks_str.split("+")
            blocks_of_file = {}
            for pair in blocks:
                block, node = pair.split(":")
                blocks_of_file[block] = node

            file_json = {"file_name": file_name, 'owner': owner, 'state': state, 'size': size, 'file_hash': file_hash,
                         'blocks_of_file': blocks_of_file, 'checksums': checksums, 'data_bytes': data_bytes,
                         'oti_common': oti_common, 'oti_scheme': oti_scheme, 'last_update': last_update}

            #head = {'checksums': {"sha256": checksums}, 'data_bytes': int(data_bytes), 'oti_common': int(oti_common), 'oti_scheme': int(oti_scheme)}

            return file_json

        except BaseException:
            return None
        except ValueError:
            raise InternalError("Failed to deserialize game data")

    def _send_request(self,
                      suffix,
                      data=None,
                      content_type=None,
                      name=None,
                      auth_user=None,
                      auth_password=None):
        if self._base_url.startswith("http://"):
            url = "{}/{}".format(self._base_url, suffix)
        else:
            url = "http://{}/{}".format(self._base_url, suffix)

        headers = {}
        if auth_user is not None:
            auth_string = "{}:{}".format(auth_user, auth_password)
            b64_string = b64encode(auth_string.encode()).decode()
            auth_header = 'Basic {}'.format(b64_string)
            headers['Authorization'] = auth_header

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if result.status_code == 404:
                raise XoException("No such game: {}".format(name))

            if not result.ok:
                raise XoException("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise XoException(
                'Failed to connect to {}: {}'.format(url, str(err)))

        except BaseException as err:
            raise XoException(err)

        return result.text

    def _send_xo_txn(self,
                     name,
                     address,
                     payload_object,
                     action,
                     wait=None,
                     auth_user=None,
                     auth_password=None):

        if payload_object is None:
            payload_object = name

        json_payload = json.dumps({'action': action, 'payload': payload_object})
        payload = json_payload.encode()

        header = TransactionHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            family_name="hdfssb",
            family_version="1.0",
            inputs=[address],
            outputs=[address],
            dependencies=[],
            payload_sha512=_sha512(payload),
            batcher_public_key=self._signer.get_public_key().as_hex(),
            nonce=hex(random.randint(0, 2 ** 64))
        ).SerializeToString()

        signature = self._signer.sign(header)

        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=signature
        )

        batch_list = self._create_batch_list([transaction])
        batch_id = batch_list.batches[0].header_signature

        if wait and wait > 0:
            wait_time = 0
            start_time = time.time()
            response = self._send_request(
                "batches", batch_list.SerializeToString(),
                'application/octet-stream',
                auth_user=auth_user,
                auth_password=auth_password)
            while wait_time < wait:
                status = self._get_status(
                    batch_id,
                    wait - int(wait_time),
                    auth_user=auth_user,
                    auth_password=auth_password)
                wait_time = time.time() - start_time

                if status != 'PENDING':
                    return response

            return response

        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream',
            auth_user=auth_user,
            auth_password=auth_password)

    def _create_batch_list(self, transactions):
        transaction_signatures = [t.header_signature for t in transactions]

        header = BatchHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            transaction_ids=transaction_signatures
        ).SerializeToString()

        signature = self._signer.sign(header)

        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature)
        return BatchList(batches=[batch])

    def wait_for_transaction(self, link):
        link = json.loads(link)["link"]
        status = "PENDING"
        limit = 30
        numer_attamps = 0
        while status == "PENDING" and numer_attamps < limit:
            result = requests.get(link)
            text_result = json.loads(result.text)
            status = text_result["data"][0]["status"]
            print(status)
            numer_attamps += 1

