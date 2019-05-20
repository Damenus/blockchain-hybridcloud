
class File:
    def __init__(self, name, board, state, player1, player2):
        self.name = name
        self.owner = board
        self.state = state
        self.users = []
        self.pice_of_file = {} # as23d1:10.1.1.0, da1d2:10.1.1.1
        self.file_hash = player1
        self.pokolei_kawalki = []
