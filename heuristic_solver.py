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

        # solved_board_squares = game_state.board.squares
        
        options = list(range(1, self.N + 1))
        options_board_squares = [options if x == 0 else [x] for x in board_squares]

        print(f'self.N: {self.N}')
        print(f'self.m: {self.m}')
        print(f'self.n: {self.n}')
        print(f'options: {options}')
        print(f'board_squares: {board_squares}')
        # print(f'solved_board_squares: {solved_board_squares}')
        print(f'options_board_squares: {options_board_squares}')

        changes = True
        while changes:
            basic_changes = True

            while basic_changes:
                options_board_squares, changes_rows = self.check_rows(options_board_squares)
                options_board_squares, changes_columns = self.check_columns(options_board_squares)
                options_board_squares, changes_blocks = self.check_blocks(options_board_squares)

                basic_changes = changes_rows or changes_columns or changes_blocks
                print(f'basic_changes: {basic_changes}')

            print(f'options_board_squares: {options_board_squares}')

            options_board_squares, hidden_single_changes = self.find_hidden_single(options_board_squares)
            print(f'hidden_single_changes: {hidden_single_changes}')

            # if a hidden single change has been made, we need to recheck the rows, columns and blocks, so go to the next iteration of the while loop
            if hidden_single_changes:
                continue

            options_board_squares, naked_pair_changes = self.find_naked_pair(options_board_squares)
            print(f'naked_pair_changes: {naked_pair_changes}')

            if naked_pair_changes:
                continue

            changes = basic_changes or hidden_single_changes or naked_pair_changes

            print(f'changes: {changes}')

        result_board_squares = [square[0] if len(square) == 1 else 0 for square in options_board_squares]

        return result_board_squares
        

    def check_rows(self, options_board_squares):
        changes = False
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
                        changes = True
                    else:
                        output[index].append(option)
        
        return output, changes
    
    def check_columns(self, options_board_squares):
        changes = False
        output = [[] for _ in range(self.N * self.N)]
        seen_values = [[] for _ in range(self.N)]

        # for each column, get the values that are already seen
        for i in range(self.N):
            for j in range(self.N):
                index = i + j * self.N
                square = options_board_squares[index]

                if len(square) == 1:
                    output[index].append(square[0])
                    seen_values[i].append(square[0])

        # for each column update the output
        for i in range(self.N):
            for j in range(self.N):
                index = i + j * self.N
                square = options_board_squares[index]

                if len(square) == 1:
                    continue

                for option in square:
                    if option in seen_values[i]:
                        changes = True
                    else:
                        output[index].append(option)

        return output, changes
    
    def check_blocks(self, options_board_squares):
        changes = False
        output = [[] for _ in range(self.N * self.N)]
        seen_values = {block_id: [] for block_id in [(i, j) for i in range(self.n) for j in range(self.m)]}

        # get the values that are already seen for each block
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                block_id = (i // self.m, j // self.n)
                square = options_board_squares[index]

                if len(square) == 1:
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
                        changes = True
                    else:
                        output[index].append(option)

        return output, changes
    

    def find_hidden_single(self, options_board_squares):
        """
        Finds hidden singles in the Sudoku board.
        @return: updated options_board_squares and a boolean indicating if there were changes
        """
        changes = False
        # check for each row, column and block if there is an option that only appears once
        # if so, that option is a hidden single

        # check rows
        for i in range(self.N):
            row = options_board_squares[i * self.N: (i + 1) * self.N]

            for option in range(1, self.N + 1):
                count = 0
                index = -1

                for j, square in enumerate(row):
                    if len(square) == 1:
                        continue

                    if option in square:
                        count += 1
                        index = j

                if count == 1:
                    options_board_squares[i * self.N + index] = [option]
                    changes = True
        
        # check columns
        for i in range(self.N):
            column = options_board_squares[i::self.N]

            for option in range(1, self.N + 1):
                count = 0
                index = -1

                for j, square in enumerate(column):
                    if len(square) == 1:
                        continue

                    if option in square:
                        count += 1
                        index = j

                if count == 1:
                    options_board_squares[i + index * self.N] = [option]
                    changes = True

        return options_board_squares, changes


    def find_naked_pair(self, options_board_squares):
        """
        Finds naked pairs in the Sudoku board.
        @return: updated options_board_squares and a boolean indicating if there were changes
        """
        changes = False

        # check for each row, column and block if there are two squares with the same two options
        # if so, those two options are a naked pair and can be removed from the other squares

        # check rows
        for i in range(self.N):
            row = options_board_squares[i * self.N: (i + 1) * self.N]
            seen_pairs = []

            for j in range(self.N):
                square = row[j]

                if len(square) == 2:
                    if square in seen_pairs:
                        for k in range(self.N):
                            if row[k] != square:
                                for option in square:
                                    if option in row[k]:
                                        options_board_squares[i * self.N + k].remove(option)
                                        changes = True
                    else:
                        seen_pairs.append(square)
                else:
                    seen_pairs.append(square)

        # check columns
        for i in range(self.N):
            column = options_board_squares[i::self.N]
            seen_pairs = []

            for j in range(self.N):
                square = column[j]

                if len(square) == 2:
                    if square in seen_pairs:
                        for k in range(self.N):
                            if column[k] != square:
                                for option in square:
                                    if option in column[k]:
                                        options_board_squares[i + k * self.N].remove(option)
                                        changes = True
                    else:
                        seen_pairs.append(square)
                else:
                    seen_pairs.append(square)
        
        # check blocks
        block_squares = {block_id: [] for block_id in [(i, j) for i in range(self.n) for j in range(self.m)]}

        # get the squares for each block
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                block_id = (i // self.m, j // self.n)
                block_squares[block_id].append(options_board_squares[index])

        for block_id in block_squares:
            seen_pairs = []

            for square in block_squares[block_id]:
                if len(square) == 2:
                    if square in seen_pairs:
                        for k in range(self.N):
                            if block_squares[block_id][k] != square:
                                for option in square:
                                    if option in block_squares[block_id][k]:
                                        options_board_squares[block_id[0] * self.m + k // self.n * self.N + k % self.m].remove(option)
                                        changes = True
                    else:
                        seen_pairs.append(square)

        return options_board_squares, changes


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
    game_state.board.squares = solver.evaluate_entries(game_state)
    end = time.time()

    print(f'Time taken: {end - start} seconds')

    print(game_state.board)

