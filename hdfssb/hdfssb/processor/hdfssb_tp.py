import traceback
import sys
import hashlib
import logging
import json

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "simplewallet"


def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()


# Prefix for simplewallet is the first six hex digits of SHA-512(TF name).
sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]


class File:
    def __init__(self, name, board, state, player1, player2):
        self.name = name
        self.owner = board
        self.state = state
        self.users = []
        self.pice_of_file = {}  # as23d1:10.1.1.0, da1d2:10.1.1.1
        self.file_hash = player1
        self.pokolei_kawalki = []


class SpaceStorage:
    def __init__(self, node_name, capacity, taken_space, reversed_space, last_update):
        self.node_name = node_name  # 10.12.1.1:{capacity:12341; taken:132; reserved:123; last_update:15001231242}
        self.capacity = capacity
        self.taken_space = taken_space
        self.reversed_space = reversed_space
        self.last_update = last_update


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
        return [self._namespace_prefix]

    def apply(self, transaction, context):

        # Get the payload and extract simplewallet-specific information.
        header = transaction.header
        payload_map = json.loads(transaction.payload.decode())
        LOGGER.info("---------\n" + str(payload_map))
        # operation = payload_map.operation
        # amount = payload_map.amount
        operation = payload_map['action']

        # Get the public key sent from the client.
        from_key = header.signer_public_key

        # Perform the operation.
        LOGGER.info("Operation = " + operation)

        # if operation == "deposit":
        #     self._make_deposit(context, amount, from_key)
        # elif operation == "withdraw":
        #     self._make_withdraw(context, amount, from_key)
        # elif operation == "transfer":
        #     to_key = payload_map.to_key
        #     self._make_transfer(context, amount, to_key, from_key)
        # else:
        #     LOGGER.info("Unhandled action. " +
        #                 "Operation should be deposit, withdraw or transfer")

        if operation == "reserve_storage":
            self._reserve_storage(context, payload_map, from_key)
        elif operation == "":
            pass
        else:
            LOGGER.info("Unhandled action.")

    def _reserve_storage(self, context, payload_map, from_key):
        wallet_address = self._get_wallet_address(from_key)
        current_entry = context.get_state([wallet_address])
        if current_entry == []:
            new_balance = int(0)
        else:
            balance = int(current_entry[0].data)
            new_balance = int(0) + int(1)

        state_data = str(new_balance).encode('utf-8')
        addresses = context.set_state({wallet_address: state_data})
        pass

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
        handler = SimpleWalletTransactionHandler(sw_namespace)
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
