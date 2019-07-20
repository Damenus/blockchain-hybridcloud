import hashlib
import logging

from sawtooth_sdk.processor.exceptions import InternalError

LOGGER = logging.getLogger(__name__)

FAMILY_NAME_NAMESPACE = hashlib.sha512('hdfssb'.encode("utf-8")).hexdigest()[0:6]
NODE_NAMESPACE = hashlib.sha512('node'.encode("utf-8")).hexdigest()[0:4]


def make_node_address(name):
    return FAMILY_NAME_NAMESPACE + NODE_NAMESPACE + hashlib.sha512(name.encode('utf-8')).hexdigest()[0:60]


# /root/{cluster_name}/{node_name}
# 10.12.1.1:{capacity:12341; taken:132; reserved:123; last_update:15001231242}
# storage volume
class Node:
    def __init__(self, node_name, cluster, capacity, taken_space, reversed_space, last_update):
        self.node_name = node_name
        self.cluster = cluster
        self.capacity = capacity
        self.taken_space = taken_space
        self.reversed_space = reversed_space
        self.last_update = last_update


class NodeState:

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
        address = make_node_address(game_name)

        state_data = self._serialize(games)

        self._address_cache[address] = state_data

        self._context.set_state(
            {address: state_data},
            timeout=self.TIMEOUT)

    def _delete_node(self, game_name):
        address = make_node_address(game_name)

        self._context.delete_state(
            [address],
            timeout=self.TIMEOUT)

        self._address_cache[address] = None

    def _load_nodes(self, node_name):
        address = make_node_address(node_name)

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

        nodes = {}
        try:
            for node in data.decode().split("|"):
                node_name, cluster, capacity, taken_space, reversed_space, last_update = node.split(",")

                nodes[node_name] = Node(node_name, cluster, capacity, taken_space, reversed_space, last_update)
        except ValueError:
            raise InternalError("Failed to deserialize game data")

        return nodes

    def _serialize(self, nodes):
        """Takes a dict of game objects and serializes them into bytes.

        Args:
            games (dict): game name (str) keys, Game values.

        Returns:
            (bytes): The UTF-8 encoded string stored in state.
        """

        node_strs = []
        for name, g in nodes.items():
            node_str = ",".join(
                [name, str(g.cluster), str(g.capacity), str(g.taken_space), str(g.reversed_space), str(g.last_update)])
            node_strs.append(node_str)

        return "|".join(sorted(node_strs)).encode()
