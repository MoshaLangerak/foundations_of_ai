class HeuristicSolver():
    def __init__(self, game_state) -> None:
        self.m = game_state.board.m
        self.n = game_state.board.n
        self.N = game_state.board.N

        self.board_squares = game_state.board.squares


    def get_moves(self):
        """
        Uses the heuristic solver function and translates the output to a list of moves.
        @return: list of solving moves and list of non-solving moves
        """
        options = list(range(1, self.N + 1))
        options_board_squares = [options if x == 0 else [x] for x in self.board_squares]

        options_board_squares, _ = self.check_options(options_board_squares)

        # if somehow the board contains a unvalid move, return empty lists
        try:
            solved_board_squares, result_options_board_squares = self.solve(options_board_squares)
        except Exception as e:
            print(e)
            return [], []

        solving_moves = []
        for i in range(self.N * self.N):
            if self.board_squares[i] == 0 and solved_board_squares[i] != 0:
                solving_moves.append([(i // self.N, i % self.N), solved_board_squares[i]])

        non_solving_moves = []
        for i in range(self.N * self.N):
            if solved_board_squares[i] != 0 and len(options_board_squares[i]) > 1:
                for option in options_board_squares[i]:
                    if option != solved_board_squares[i]:
                        non_solving_moves.append([(i // self.N, i % self.N), option])

        for i in range(self.N * self.N):
            if len(result_options_board_squares[i]) != len(options_board_squares[i]):
                for option in options_board_squares[i]:
                    if option not in result_options_board_squares[i]:
                        if [(i // self.N, i % self.N), option] not in non_solving_moves:
                           non_solving_moves.append([(i // self.N, i % self.N), option])

        return solving_moves, non_solving_moves


    def solve_board(self, board_squares):
        """
        Converts the board squares to options and solves the board.
        @return: list of solved board squares and list of options for each square
        """
        options = list(range(1, self.N + 1))
        options_board_squares = [options if x == 0 else [x] for x in board_squares]

        return self.solve(options_board_squares)


    def solve(self, options_board_squares):
        """
        Reduces the options provided using the hueristic rules. 
        @return: list of taboo moves
        """
        changes = True

        while changes:
            basic_changes = True

            while basic_changes:
                options_board_squares, basic_changes = self.check_options(options_board_squares)

            options_board_squares, hidden_single_changes = self.find_hidden_single(options_board_squares)

            # if a hidden single change has been made, we need to recheck the rows, columns and blocks, so go to the next iteration of the while loop
            if hidden_single_changes:
                continue

            # check for naked pairs
            options_board_squares, naked_pair_changes = self.find_naked_tuple(options_board_squares, 2)

            if naked_pair_changes:
                continue

            # check for naked triples
            options_board_squares, naked_triple_changes = self.find_naked_tuple(options_board_squares, 3)

            if naked_triple_changes:
                continue

            # check for naked quadruples
            options_board_squares, naked_quadruple_changes = self.find_naked_tuple(options_board_squares, 4)

            if naked_quadruple_changes:
                continue

            changes = basic_changes or hidden_single_changes or naked_pair_changes

        solved_board_squares = [square[0] if len(square) == 1 else 0 for square in options_board_squares]

        return solved_board_squares, options_board_squares
    

    def check_options(self, options_board_squares):
        """
        Reduces the options in a board based on the basic rules of Sudoku.
        @return: updated options_board_squares and a boolean indicating if there were changes
        """
        options_board_squares, changes_rows = self.check_rows(options_board_squares)
        options_board_squares, changes_columns = self.check_columns(options_board_squares)
        options_board_squares, changes_blocks = self.check_blocks(options_board_squares)

        return options_board_squares, changes_rows or changes_columns or changes_blocks
    

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


    def find_naked_tuple(self, options_board_squares, tuple_size):
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
            seen_tuples = {}

            for j in range(self.N):
                square = tuple(row[j])
                if len(square) == tuple_size:
                    if square in seen_tuples:
                        seen_tuples[square] += 1
                        if seen_tuples[square] == tuple_size:
                            for k in range(self.N):
                                if tuple(row[k]) != square:
                                    for option in square:
                                        if option in row[k]:
                                            options_board_squares[i * self.N + k].remove(option)
                                            changes = True
                    else:
                        seen_tuples[square] = 1

        # check columns
        for i in range(self.N):
            column = options_board_squares[i::self.N]
            seen_tuples = {}

            for j in range(self.N):
                square = tuple(column[j])

                if len(square) == tuple_size:
                    if square in seen_tuples:
                        seen_tuples[square] += 1
                        if seen_tuples[square] == tuple_size:
                            for k in range(self.N):
                                if tuple(column[k]) != square:
                                    for option in square:
                                        if option in column[k]:
                                            options_board_squares[i + k * self.N].remove(option)
                                            changes = True
                    else:
                        seen_tuples[square] = 1
        
        # check blocks
        block_squares = {block_id: [] for block_id in [(i, j) for i in range(self.n) for j in range(self.m)]}

        # get the squares for each block
        for i in range(self.N):
            for j in range(self.N):
                index = i * self.N + j
                block_id = (i // self.m, j // self.n)
                block_squares[block_id].append(options_board_squares[index])

        for block_id in block_squares:
            seen_tuples = {}

            for square in block_squares[block_id]:
                square = tuple(square)
                if len(square) == tuple_size:
                    if square in seen_tuples:
                        seen_tuples[square] += 1
                        if seen_tuples[square] == tuple_size:
                            for k in range(self.N):
                                if tuple(block_squares[block_id][k]) != square:
                                    for option in square:
                                        if option in block_squares[block_id][k]:
                                            options_board_squares[block_id[0] * self.m + k // self.n * self.N + k % self.m].remove(option)
                                            changes = True
                    else:
                        seen_tuples[square] = 1

        return options_board_squares, changes
