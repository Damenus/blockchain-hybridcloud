from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction

class FileDescriptionTransactionHandler(TransactionHandler):
    def __init__(self, namespace_prefix):
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        return 'hdfssb'

    @property
    def family_versions(self):
        return ['0.1']

    @property
    def namespaces(self):
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        header = transaction.header
        signer = header.signer_public_key

        fd_payload = FileDescriptionPayload.from_bytes(transaction.payload)

        fd_state = FileDescriptionState(context)

        if fd_payload.action == 'delete':
            game = fd_state.get_game(fd_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: game does not exist')

            fd_state.delete_game(fd_payload.name)