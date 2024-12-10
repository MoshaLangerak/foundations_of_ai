from pathlib import Path

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove, parse_game_state
from team11_A2.valid_entry_finder import ValidEntryFinder

class HeuristicSolver():

    def __init__(self, game_state) -> None:
        self.m = game_state.board.m
        self.n = game_state.board.n
        self.N = game_state.board.N

    def evaluate_entries(self, game_state: GameState):
        """
        Evaluates each valid entry based on heuristic rules to see if it is a taboo move or not.
        @return: list of taboo moves
        """

        # attributes from SudokuBoard
        # N = m * n
        # self.m = m
        # self.n = n
        # self.N = N     # N = m * n, numbers are in the range [1, ..., N]
        # self.squares = [SudokuBoard.empty] * (N * N)
        # square2index(self, square: Square) -> int
        # def index2square(self, k: int) -> Square

        board_squares = game_state.board.squares

        solved_board_squares = game_state.board.squares
        
        options = list(range(1, self.N + 1))
        options_board_squares = [options if x == 0 else [x] for x in board_squares]

        print(f'self.N: {self.N}')
        print(f'self.m: {self.m}')
        print(f'self.n: {self.n}')
        print(f'options: {options}')
        print(f'board_squares: {board_squares}')
        print(f'solved_board_squares: {solved_board_squares}')
        print(f'options_board_squares: {options_board_squares}')

        options_board_squares = self.check_rows(options_board_squares)
        options_board_squares = self.check_columns(options_board_squares)
        options_board_squares = self.check_blocks(options_board_squares)

        print(f'options_board_squares: {options_board_squares}')

        while True:
            
            break
            # naked_singles = self.find_naked_single()
            # hidden_singles = self.find_hidden_single()

    def check_rows(self, options_board_squares):
        output = [[] for _ in range(self.N * self.N)]
        seen_values = [[] for _ in range(self.N)]

        # for each row, get the values that are already seen
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                square = options_board_squares[index]

                if len(square) == 1:
                    output[index].append(square[0])
                    seen_values[i].append(square[0])

        # for each row update the output
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                square = options_board_squares[index]

                if len(square) == 1:
                    continue

                for option in square:
                    if option in seen_values[i]:
                        pass
                    else:
                        output[index].append(option)
        
        return output
    
    def check_columns(self, options_board_squares):
        output = [[] for _ in range(self.N * self.N)]
        seen_values = [[] for _ in range(self.N)]

        # for each column, get the values that are already seen
        for i in range(self.N):
            for j in range(self.N):
                index = i + j * self.N
                square = options_board_squares[index]

                if len(square) == 1:
                    output[index].append(square[0])
                    seen_values[j].append(square[0])

        # for each column update the output
        for i in range(self.N):
            for j in range(self.N):
                index = i + j * self.N
                square = options_board_squares[index]

                if len(square) == 1:
                    continue

                for option in square:
                    if option in seen_values[j]:
                        pass
                    else:
                        output[index].append(option)

        return output
    
    def check_blocks(self, options_board_squares):
        # Initialize the output and seen values for each block
        output = [[] for _ in range(self.N * self.N)]
        seen_values = {block_id: [] for block_id in [(i, j) for i in range(self.n) for j in range(self.m)]}

        # get the values that are already seen for each block
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                block_id = (i // self.m, j // self.n)  # Calculate the block ID
                square = options_board_squares[index]

                if len(square) == 1:  # If the square is solved
                    output[index].append(square[0])
                    seen_values[block_id].append(square[0])

        # for each block update the output
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                block_id = (i // self.m, j // self.n)
                square = options_board_squares[index]

                if len(square) == 1:
                    continue

                for option in square:
                    if option in seen_values[block_id]:
                        pass
                    else:
                        output[index].append(option)

        return output


    def find_naked_single(self):
        """
        Finds nakes singles in the Sudoku board.
        @return: list of naked singles
        """
        pass
    
    def find_hidden_single(self):
        """
        Finds hidden singles in the Sudoku board.
        @return: list of hidden singles
        """
        
        # check for each row, column and square whether there is an option that only appears once
        hidden_singles = []

        # check for each row
        for row in range(self.board.N):
            for option in self.options:
                count = 0
                index = 0
                for i in range(self.board.N):
                    if self.board.squares[self.board.square2index((row, i))] == option:
                        count += 1
                        index = i

                        if count > 1:
                            break
                    
                if count == 1:
                    hidden_singles.append((row, index), option)


if __name__ == "__main__":
    import time

    # board_file = 'boards/empty-2x3.txt'
    # board_file = 'boards/test-2x2.txt'
    board_file = 'boards/test-3x3.txt'

    text = Path(board_file).read_text()
    game_state = parse_game_state(text, 'rows')

    print(game_state.board)

    print(game_state.board.squares)

    start = time.time()
    solver = HeuristicSolver(game_state)
    solver.evaluate_entries(game_state)
    end = time.time()

    print(f'Time taken: {end - start} seconds')