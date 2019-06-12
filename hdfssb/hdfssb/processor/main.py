import traceback
import sys
import hashlib
import logging

from sawtooth_sdk.processor.core import TransactionProcessor
from hdfssb.hdfssb.processor.handler import XoTransactionHandler

def main():
    try:
        # In docker, the url would be the validator's container name with
        # port 4004
        processor = TransactionProcessor(url='tcp://127.0.0.1:4004')

        handler = XoTransactionHandler()

        processor.add_handler(handler)

        processor.start()
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
