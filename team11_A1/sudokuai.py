#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
import copy
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, game_state: GameState):
        return game_state.scores[0] - game_state.scores[1]
    
    def getChildren(self, game_state: GameState):
        valid_entries = ValidEntryFinder(game_state).get_pos_entries()

        if valid_entries is None:
            return None
        
        children = []
        for square in valid_entries:
            for entry in valid_entries[square]:
                move = Move(square, entry)
                new_game_state = GameStateManager().add_move_to_game_state(game_state, move)
                children.append(new_game_state)
    
        return children
    
    def minimax(self, game_state: GameState, depth, alpha, beta, maximizingPlayer):
        children = self.getChildren(game_state)
        
        if depth == 0 or not children:
            return self.evaluate(game_state)

        if maximizingPlayer:
            maxEval = -float('inf')
            for child in children:
                eval = self.minimax(child, depth-1, alpha, beta, False)
                maxEval = max(maxEval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    print('Pruning')
                    break
            return maxEval
        else:
            minEval = float('inf')
            for child in children:
                eval = self.minimax(child, depth-1, alpha, beta, True)
                minEval = min(minEval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    print('Pruning')
                    break
            return minEval
    
    def compute_best_move(self, game_state: GameState) -> None:
        # implementation based on naive_player, will propose moves with increasing depth
        valid_entries = ValidEntryFinder(game_state).get_pos_entries()
        all_moves = [Move((i, j), value) for (i, j) in valid_entries for value in valid_entries[(i, j)]] # ! This could be moved into the entryfinder class

        is_maximizing = self.player_number == 1

        print(f'Player {self.player_number} is maximizing: {is_maximizing}')
        print("Played taboo moves: ", ", ".join(str(move) for move in game_state.taboo_moves), "\n")

        # set the maximum depth for iterative deepening
        max_depth = 10

        for depth in range(0, max_depth + 1):
            best_score = -float('inf') if is_maximizing else float('inf')
            best_move = None
            alpha = -float('inf')
            beta = float('inf')
            
            print(f'Checking all moves with depth {depth}')

            for i, move in enumerate(all_moves):
                print(f'Checking move {i}: {move.square} -> {move.value}')
                new_game_state = GameStateManager().add_move_to_game_state(game_state, move)
                score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)

                if i == 0:
                    print(f'Score for move {move.square} -> {move.value} is {score}, best score is {best_score} (inf/-inf expected)')
                else:
                    print(f'Score for move {move.square} -> {move.value} is {score}, best score is {best_score}')

                if is_maximizing:
                    if score > best_score and not score == float('inf'):
                        best_score = score
                        best_move = move
                        print(f'New best move: {best_move.square} -> {best_move.value} with score {best_score}')

                        # if depth is 0, we can propose the move immediately
                        if depth == 0:
                            self.propose_move(best_move)
                else:
                    if score < best_score and not score == float('-inf'):
                        best_score = score
                        best_move = move
                        print(f'New best move: {best_move.square} -> {best_move.value} with score {best_score}')

                        # if depth is 0, we can propose the move immediately
                        if depth == 0:
                            self.propose_move(best_move)
            
            # only propose a move when all moves of the current depth have been checked <-- this is a design choice
            self.propose_move(best_move)
            print(f'Best move proposed: {best_move.square} -> {best_move.value} with score {best_score}')


class GameStateManager():

    def __init__(self) -> None:
        pass

    def add_move_to_game_state(self, game_state: GameState, move: Move):
        """
        Adds a move to the game state and returns the new game state.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        @param move: Move object representing the move to be added to the game state.
        @return: new GameState object with the move added to the game state.
        """
        new_game_state = copy.deepcopy(game_state)
        new_game_state.board.put(move.square, move.value)
        new_game_state.moves.append(move)
        new_game_state.current_player = 3 - new_game_state.current_player

        number_of_completions = 0
        if self.check_row_completions(game_state, move):
            number_of_completions += 1
        if self.check_col_completions(game_state, move):
            number_of_completions += 1
        if self.check_square_completions(game_state, move):
            number_of_completions += 1
        
        scores_dict = {0: 0, 1: 1, 2: 3, 3: 7}

        new_game_state.scores[game_state.current_player - 1] += scores_dict[number_of_completions]

        return new_game_state

    def check_row_completions(self, game_state: GameState, move: Move):
        """
        Check if a move completes a row.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        @param move: Move object representing the move to be added to the game state.
        @return: True if the move completes a row, False otherwise.
        """
        row = move.square[0]
        row_values = set(game_state.board.get((row, col)) for col in range(game_state.board.n * game_state.board.m) if game_state.board.get((row, col)) != 0)
        available_entries = set(range(1, game_state.board.n * game_state.board.m + 1))
        row_values.add(move.value)
        return row_values == available_entries
        

    def check_col_completions(self, game_state: GameState, move: Move):
        """
        Check if a move completes a column.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        @param move: Move object representing the move to be added to the game state.
        @return: True if the move completes a column, False otherwise.
        """
        col = move.square[1]
        col_values = set(game_state.board.get((row, col)) for row in range(game_state.board.n * game_state.board.m) if game_state.board.get((row, col)) != 0)
        available_entries = set(range(1, game_state.board.n * game_state.board.m + 1))
        col_values.add(move.value)
        return col_values == available_entries

    def check_square_completions(self, game_state: GameState, move: Move):
        """
        Check if a move completes a square.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        @param move: Move object representing the move to be added to the game state.
        @return: True if the move completes a square, False otherwise.
        """
        row = move.square[0] // game_state.board.m
        col = move.square[1] // game_state.board.n
        square_values = set(
            game_state.board.get((row * game_state.board.m + i, col * game_state.board.n + j))
            for i in range(game_state.board.m)
            for j in range(game_state.board.n)
            if game_state.board.get((row * game_state.board.m + i, col * game_state.board.n + j)) != 0
        )
        available_entries = set(range(1, game_state.board.n * game_state.board.m + 1))
        square_values.add(move.value)
        return square_values == available_entries

class ValidEntryFinder:

    def __init__(self,game_state: GameState):
        """
        Initialize attributes from the game_state object.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        """
        # initialize game_state object attributes
        self.board = game_state.board
        self.taboo_moves = game_state.taboo_moves

        # get all occupied squares
        self.occupied_squares = set(game_state.occupied_squares1) | set(game_state.occupied_squares2)

        # get the allowed squares attributes for the correct player and exclude the occupied squares
        # self.allowed_squares = (
        #     set(game_state.allowed_squares1) if game_state.current_player == 1 else set(game_state.allowed_squares2)
        # ) - self.occupied_squares
        self.allowed_squares = set(game_state.player_squares()) - self.occupied_squares

        # initialize board size # ! can maybe be optimized by using SudokuBoard class methods
        self.size = self.board.n * self.board.m
        self.n = self.board.n
        self.m = self.board.m


    def squares2values(self, squares: set) -> set:
        """
        Converts coordinates to values of entries in those coordinates.
        @param squares: set of coordinates that have to be converted to their values.
        @return: set of values that correspond to the set of coordinates given.
        """
        # return set(self.board.squares[self.board.square2index(sq)] for sq in squares) - {0}
        return set(self.board.get(sq) for sq in squares) - {0}


    def get_row_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed row.
        @return: dictionary with row numbers as keys and the numbers included in the corresponding rows as values
        """
        # get all unique row coordinates in allowed_squares
        allowed_row_coordinates = set(square[0] for square in self.allowed_squares)

        # fill dictionary with numbers per row
        dct_row_nrs = {}
        for row_coord in allowed_row_coordinates:
            # get coords of entire row with row coordinate
            row_coords = set((row_coord,i) for i in range(self.size))

            # assign current values of all squares in the row to dictionary (excluding 0/. as they are not valid entry options)
            dct_row_nrs[row_coord] = self.squares2values(row_coords)

        return dct_row_nrs
    

    def get_col_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed column.
        @return: dictionary with column numbers as keys and the numbers included in the corresponding columns as values.
        """
        # get all unique column coordinates in allowed_squares
        allowed_col_coordinates = set(square[1] for square in self.allowed_squares)

        # fill dictionary with numbers per column
        dct_col_nrs = {}
        for col_coord in allowed_col_coordinates:
            # get coords of entire column with column coordinate
            current_col_coords = set((i,col_coord) for i in range(self.size))

            # assign current values of all squares in the column to dictionary (excluding 0/. as they are not valid entry options)
            dct_col_nrs[col_coord] = self.squares2values(current_col_coords)

        return dct_col_nrs
    

    def get_block_id(self, coordinate: tuple) -> int:
        """
        Get the identifier the block within which coordinate lies
        @param coordinate: tuple of the format (row, column).
        @return: identifier of the block within which coordinate lies as an integer
        """
        return (coordinate[0]//self.m) * self.m + (coordinate[1]//self.n)
        
    def get_block_coordinates(self, block_id: int) -> set[tuple]: # ! set[tuple] used here, which is not as detailed in other functions
        """
        Find all coordinates of the block with block_id.
        @param block_id: identifier of the block of which the coordinates should be found.
        @return: set of all (n*m) coordinates inside the block with block_id.
        """
        # compute starting row and column of the block
        block_row_start = (block_id // self.m) * self.m
        block_col_start = (block_id % self.m) * self.n

        # generate all coordinates within the block
        coordinates = {
            (row, col)
            for row in range(block_row_start, block_row_start + self.m)
            for col in range(block_col_start, block_col_start + self.n)
        }

        return coordinates
    
    def get_block_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed block.
        @return: dictionary with block ids as keys and the numbers included in the corresponding blocks as values.
        """
        # get all unique block ids in allowed_squares
        allowed_block_ids = set(self.get_block_id(square) for square in self.allowed_squares)

        # fill dictionary with values per block
        dct_block_nrs = {}
        for block_id in allowed_block_ids:
            # get coords of all squares in the block
            current_block_coords = self.get_block_coordinates(block_id)
            # assign current values of all squares in the block to dictionary (excluding 0/. as they are not valid entry options)
            dct_block_nrs[block_id] = self.squares2values(current_block_coords)
        
        return dct_block_nrs

        
    def get_pos_entries(self) -> dict:
        """
        Find all possible entries for the allowed squares of the current player.
        @return: dictionary with the allowed squares as keys and the possible entries in the corresponding squares as values.
        """

        # get the available entries based on the board seize
        available_entries = set(range(1, self.size+1))
        
        # get dictionary for values in each row, column, and block
        dct_row_numbers = self.get_row_dict()
        dct_col_numbers = self.get_col_dict()
        dct_block_numbers = self.get_block_dict()

        # compute possible values for each (empty) square
        dct_pos_entries = {}
        for square in self.allowed_squares:
            row_values = dct_row_numbers[square[0]]
            col_values = dct_col_numbers[square[1]]
            block_values = dct_block_numbers[self.get_block_id(square)]

            # get the values that are not possible in the current square
            present_values = row_values | col_values | block_values
            
            # compute possible entries
            pos_entries = set(
                entry for entry in (available_entries - present_values)
                if TabooMove(square, entry) not in self.taboo_moves
            )

            dct_pos_entries[square] = pos_entries
        
        return dct_pos_entries
