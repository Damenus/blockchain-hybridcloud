import hashlib
import json

from sawtooth_sdk.processor.exceptions import InternalError


FAMILY_NAME_NAMESPACE = hashlib.sha512('hdfssb'.encode("utf-8")).hexdigest()[0:6]
FILE_NAMESPACE = hashlib.sha512('file'.encode("utf-8")).hexdigest()[0:4]


def make_file_address(name):
    return FAMILY_NAME_NAMESPACE + FILE_NAMESPACE + hashlib.sha512(name.encode('utf-8')).hexdigest()[0:60]


# /{owner}/{file_name}/{block}
class File:
    def __init__(self, file_name, owner, state, size, file_hash, blocks_of_file, last_update):
        self.file_name = file_name
        self.owner = owner
        self.state = state
        # self.users_granted = []
        self.size = size
        self.file_hash = file_hash
        self.blocks_of_file = blocks_of_file  # {} as23d1:10.1.1.0, da1d2:10.1.1.1
        self.last_update = last_update


class FileState:

    TIMEOUT = 3

    def __init__(self, context):
        """Constructor.

        Args:
            context (sawtooth_sdk.processor.context.Context): Access to
                validator state from within the transaction processor.
        """

        self._context = context
        self._address_cache = {}

    def delete_node(self, node_name):
        """Delete the Game named game_name from state.

        Args:
            game_name (str): The name.

        Raises:
            KeyError: The Game with game_name does not exist.
        """

        games = self._load_nodes(node_name=node_name)

        del games[node_name]
        if games:
            self._store_node(node_name, games=games)
        else:
            self._delete_node(node_name)

    def set_game(self, game_name, game):
        """Store the game in the validator state.

        Args:
            game_name (str): The name.
            game (Game): The information specifying the current game.
        """

        games = self._load_nodes(node_name=game_name)

        games[game_name] = game

        self._store_node(game_name, games=games)

    def get_node(self, game_name):
        """Get the game associated with game_name.

        Args:
            game_name (str): The name.

        Returns:
            (Game): All the information specifying a game.
        """

        return self._load_nodes(node_name=game_name).get(game_name)

    def _store_node(self, game_name, games):
        address = make_file_address(game_name)

        state_data = self._serialize(games)

        self._address_cache[address] = state_data

        self._context.set_state(
            {address: state_data},
            timeout=self.TIMEOUT)

    def _delete_node(self, game_name):
        address = make_file_address(game_name)

        self._context.delete_state(
            [address],
            timeout=self.TIMEOUT)

        self._address_cache[address] = None

    def _load_nodes(self, node_name):
        address = make_file_address(node_name)

        if address in self._address_cache:
            if self._address_cache[address]:
                serialized_games = self._address_cache[address]
                games = self._deserialize(serialized_games)
            else:
                games = {}
        else:
            state_entries = self._context.get_state(
                [address],
                timeout=self.TIMEOUT)
            if state_entries:

                self._address_cache[address] = state_entries[0].data

                games = self._deserialize(data=state_entries[0].data)

            else:
                self._address_cache[address] = None
                games = {}

        return games

    def _deserialize(self, data):
        """Take bytes stored in state and deserialize them into Python
        Game objects.

        Args:
            data (bytes): The UTF-8 encoded string stored in state.

        Returns:
            (dict): game name (str) keys, Game values.
        """
        # return json.loads(data)

        nodes = {}
        try:
            for node in data.decode().split("|"):
                file_name, owner, state, state, size, file_hash, blocks_str, last_update = node.split(",")
                blocks = blocks_str.split("+")
                blocks_of_file = {}
                for pair in blocks:
                    block, node = pair.split(":")
                    blocks_of_file[block] = node

                nodes[file_name] = File(file_name, owner, state, size, file_hash, blocks_of_file, last_update)
        except ValueError:
            raise InternalError("Failed to deserialize game data")

        return nodes

    def _serialize(self, files):
        """Takes a dict of game objects and serializes them into bytes.

        Args:
            games (dict): game name (str) keys, Game values.

        Returns:
            (bytes): The UTF-8 encoded string stored in state.
        """
        #return json.dumps(nodes).encode() for node in nodes: json.dumps(node.__dict__)

        node_strs = []
        for name, g in files.items():
            blocks = []
            for block, node in g.blocks_of_file.items():
                blocks.append(block + ":" + node)
            blocks_str = "+".join(blocks)
            node_str = ",".join(
                [name, str(g.owner), str(g.state), str(g.state), str(g.size), str(g.file_hash), str(blocks_str),
                 str(g.last_update)]
                )
            node_strs.append(node_str)
        return "|".join(sorted(node_strs)).encode()

