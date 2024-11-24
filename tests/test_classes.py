class SudokuBoard:
    def __init__(self, n, m):
        self.n = n
        self.m = m
        self._grid = [[0 for _ in range(n*m)] for _ in range(n*m)]

    def put(self, pos, val):
        self._grid[pos[0]][pos[1]] = val

    def get(self, pos):
        return self._grid[pos[0]][pos[1]]


class TabooMove:
    def __init__(self, square, value):
        self.square = square
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, TabooMove):
            return False
        return (self.square == other.square and
                self.value == other.value)

    def __hash__(self):
        return hash((self.square, self.value))

    def __repr__(self):
        return f"TabooMove(square={self.square}, value={self.value})"


class GameState:
    def __init__(self, board, taboo_moves):
        self.board = board
        self.taboo_moves = taboo_moves
        self.occupied_squares1 = []
        self.occupied_squares2 = []
        self._player_squares = []
        self.scores = [0, 0]
        self.current_player = 1

    def player_squares(self):
        return self._player_squares
