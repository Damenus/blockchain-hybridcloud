import time
import traceback
import sys
import hashlib
import logging
import json

from hdfssb.hdfssb.processor.node import *
from hdfssb.hdfssb.processor.file import *

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = 'hdfssb'
NODE_NAMESPACE = hashlib.sha512('hdfssb'.encode("utf-8")).hexdigest()[0:6]

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()


# Prefix for simplewallet is the first six hex digits of SHA-512(TF name).
sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]

def _make_xo_address(name):
    return hashlib.sha512('hdfssb'.encode('utf-8')).hexdigest()[:6] + \
        hashlib.sha512(name.encode('utf-8')).hexdigest()[:64]

# /user/file_name/part-0
# class File:
#     def __init__(self, name, board, state, player1, player2):
#         self.name = name
#         self.owner = board
#         self.state = state
#         self.users = []
#         self.pice_of_file = {}  # as23d1:10.1.1.0, da1d2:10.1.1.1
#         self.file_hash = player1
#         self.pokolei_kawalki = []


def _get_file_address(from_key):
    return NODE_NAMESPACE + _hash('file'.encode('utf-8'))[0:4] + _hash(from_key.encode('utf-8'))[0:60]




# # /root
# class Node:
#     def __init__(self, node_name, capacity, taken_space, reversed_space, last_update):
#         self.node_name = node_name  # 10.12.1.1:{capacity:12341; taken:132; reserved:123; last_update:15001231242}
#         self.capacity = capacity
#         self.taken_space = taken_space
#         self.reversed_space = reversed_space
#         self.last_update = last_update
#
#
# def _get_node_address(self, from_key):
#     return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]


class SimpleWalletTransactionHandler(TransactionHandler):

    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [NODE_NAMESPACE, FILE_NAMESPACE]

    def apply(self, transaction, context):

        node_state = NodeState(context)
        files_state = FileState(context)

        header = transaction.header
        from_key = header.signer_public_key
        payload_map = json.loads(transaction.payload.decode())
        operation = payload_map['action']
        payload = payload_map['payload']

        LOGGER.info("Operation: " + operation)
        LOGGER.info("Key: " + from_key)
        LOGGER.info("Payload: \n" + str(payload_map))

        # node
        if operation == "reserve_storage":
            self._reserve_storage(context, payload, from_key, node_state)
        elif operation == "add_node":
            self._add_node(context, payload, from_key, node_state)
        elif operation == "delete_node":
            self._add_node(context, payload, from_key, node_state)
        # file
        elif operation == "add_file":
            self._add_file(context, payload, from_key, files_state)
        elif operation == "delete_file":
            self._add_file(context, payload, from_key, files_state)
        else:
            LOGGER.error("Unhandled action.")

    def _reserve_storage(self, context, payload_map, from_key, node_state):
        # list_nodes = node_state.get_node("/root")
        name = payload_map['payload']

        wallet_address = self._get_wallet_address(name)
        current_entry = context.get_state([wallet_address])

        LOGGER.info('Got the key {} and the wallet address {} '.format(
            from_key, wallet_address))

        if current_entry == []:
            LOGGER.info('No previous deposits, creating new deposit {} '
                        .format(from_key))
        else:
            balance = int(current_entry[0].data)
            LOGGER.info('Deposit {} '.format(balance))

    def _add_node(self, context, payload_map, from_key, node_state):

        name = payload_map['node_name']
        capacity = payload_map['capacity']
        taken_space = payload_map['taken_space']
        reversed_space = payload_map['reversed_space']
        last_update = payload_map['last_update']

        node = Node(node_name=name, capacity=capacity, taken_space=taken_space, reversed_space=reversed_space, last_update=last_update)
        list_nodes = node_state.set_game(name, node)

        node_name_address = self._get_wallet_address(name)
        LOGGER.info('Node name: {} Address: {} '.format(name, node_name_address))

    def _add_file(self, context, payload_map, from_key, files_state):

        name = payload_map['file_name']
        owner = payload_map['owner']
        state = payload_map['state']
        size = payload_map['size']
        file_hash = payload_map['file_hash']
        blocks_of_file = payload_map['blocks_of_file']
        checksums = payload_map['checksums']
        data_bytes = payload_map['data_bytes']
        oti_common = payload_map['oti_common']
        oti_scheme = payload_map['oti_scheme']
        last_update = payload_map['last_update']

        file = File(file_name=name, owner=owner, state=state, size=size, file_hash=file_hash,
                    blocks_of_file=blocks_of_file, checksums=checksums, data_bytes=data_bytes, oti_common=oti_common, oti_scheme=oti_scheme, last_update=last_update)
        list_nodes = files_state.set_game(name, file)

        node_name_address = _get_file_address(name)
        LOGGER.info('Node name: {} Address: {} '.format(name, node_name_address))


    def _make_deposit(self, context, amount, from_key):
        wallet_address = self._get_wallet_address(from_key)
        LOGGER.info('Got the key {} and the wallet address {} '.format(
            from_key, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_balance = 0

        if current_entry == []:
            LOGGER.info('No previous deposits, creating new deposit {} '
                        .format(from_key))
            new_balance = int(amount)
        else:
            balance = int(current_entry[0].data)
            new_balance = int(amount) + int(balance)

        state_data = str(new_balance).encode('utf-8')
        addresses = context.set_state({wallet_address: state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_withdraw(self, context, amount, from_key):
        wallet_address = self._get_wallet_address(from_key)
        LOGGER.info('Got the key {} and the wallet address {} '.format(
            from_key, wallet_address))
        current_entry = context.get_state([wallet_address])
        new_balance = 0

        if current_entry == []:
            LOGGER.info('No user with the key {} '.format(from_key))
        else:
            balance = int(current_entry[0].data)
            if balance < int(amount):
                raise InvalidTransaction('Not enough money. The amount ' +
                                         'should be lesser or equal to {} '.format(balance))
            else:
                new_balance = balance - int(amount)

        LOGGER.info('Withdrawing {} '.format(amount))
        state_data = str(new_balance).encode('utf-8')
        addresses = context.set_state(
            {self._get_wallet_address(from_key): state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    def _make_transfer(self, context, transfer_amount, to_key, from_key):
        transfer_amount = int(transfer_amount)
        if transfer_amount <= 0:
            raise InvalidTransaction("The amount cannot be <= 0")

        wallet_address = self._get_wallet_address(from_key)
        wallet_to_address = self._get_wallet_address(to_key)
        LOGGER.info('Got the from key {} and the from wallet address {} '.format(
            from_key, wallet_address))
        LOGGER.info('Got the to key {} and the to wallet address {} '.format(
            to_key, wallet_to_address))
        current_entry = context.get_state([wallet_address])
        current_entry_to = context.get_state([wallet_to_address])
        new_balance = 0

        if current_entry == []:
            LOGGER.info('No user (debtor) with the key {} '.format(from_key))
        if current_entry_to == []:
            LOGGER.info('No user (creditor) with the key {} '.format(to_key))

        balance = int(current_entry[0].data)
        balance_to = int(current_entry_to[0].data)
        if balance < transfer_amount:
            raise InvalidTransaction('Not enough money. ' +
                                     'The amount should be less or equal to {} '.format(balance))
        else:
            LOGGER.info("Debiting balance with {}".format(transfer_amount))
            update_debtor_balance = balance - int(transfer_amount)
            state_data = str(update_debtor_balance).encode('utf-8')
            context.set_state({wallet_address: state_data})
            update_beneficiary_balance = balance_to + int(transfer_amount)
            state_data = str(update_beneficiary_balance).encode('utf-8')
            context.set_state({wallet_to_address: state_data})

    def _get_wallet_address(self, from_key):
        return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + _hash(from_key.encode('utf-8'))[0:64]


def setup_loggers():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)


def main():
    setup_loggers()
    try:
        dd = sys.argv[2]
        processor = TransactionProcessor(url=dd)
        handler = SimpleWalletTransactionHandler(NODE_NAMESPACE)
        processor.add_handler(handler)

        processor.start()

    except KeyboardInterrupt:
        LOGGER.error("KeyboardInterrupt")
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
