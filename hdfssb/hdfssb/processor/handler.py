from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError

class XoTransactionHandler(TransactionHandler):
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

    # transaction is an instance of the class Transaction that is created from the protobuf definition
    # transaction holds the command that is to be executed (e.g. taking a space or creating a game),
    # context is an instance of the class Context from the python SDK.
    # context stores information about the current state of the game (e.g. the board layout and whose turn it is).
    # Gra planszowa, stan planszy to konteks, a tura to transaction
    def apply(self, transaction, context):
        header = transaction.header
        signer = header.signer_public_key

        xo_payload = XoPayload.from_bytes(transaction.payload)

        xo_state = XoState(context)

        if xo_payload.action == 'delete':
            game = xo_state.get_game(xo_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: game does not exist')

            xo_state.delete_game(xo_payload.name)

        elif xo.payload.action == 'create':
            if xo_state.get_game(xo_payload.name) is not None:
                raise InvalidTransaction(
                    'Invalid action: Game already exists: {}'.format(
                        xo_payload.name))

            game = Game(name=xo_payload.name,
                        board="-" * 9,
                        state="P1-NEXT",
                        player1="",
                        player2="")

            xo_state.set_game(xo_payload.name, game)
            _display("Player {} created a game.".format(signer[:6]))

        elif xo.payload.action == 'take':
            game = xo_state.get_game(xo_payload.name)

            if game is None:
                raise InvalidTransaction(
                    'Invalid action: Take requires an existing game')

            if game.state in ('P1-WIN', 'P2-WIN', 'TIE'):
                raise InvalidTransaction('Invalid Action: Game has ended')

            if (game.player1 and game.state == 'P1-NEXT' and
                game.player1 != signer) or \
                    (game.player2 and game.state == 'P2-NEXT' and
                     game.player2 != signer):
                raise InvalidTransaction(
                    "Not this player's turn: {}".format(signer[:6]))

            if game.board[xo_payload.space - 1] != '-':
                raise InvalidTransaction(
                    'Invalid Action: space {} already taken'.format(
                        xo_payload))

            if game.player1 == '':
                game.player1 = signer

            elif game.player2 == '':
                game.player2 = signer

            upd_board = _update_board(game.board,
                                      xo_payload.space,
                                      game.state)

            upd_game_state = _update_game_state(game.state, upd_board)

            game.board = upd_board
            game.state = upd_game_state

            xo_state.set_game(xo_payload.name, game)
            _display(
                "Player {} takes space: {}\n\n".format(
                    signer[:6],
                    xo_payload.space) +
                _game_data_to_str(
                    game.board,
                    game.state,
                    game.player1,
                    game.player2,
                    xo_payload.name))

        else:
            raise InvalidTransaction('Unhandled action: {}'.format(
                xo_payload.action))