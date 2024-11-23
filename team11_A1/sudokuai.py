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
        valid_entries = ValidEntryFinder().get_pos_entries_boards(game_state.player_squares(), game_state.board)

        if valid_entries is None:
            return None
        
        children = []
        for square in valid_entries:
            for entry in valid_entries[square]:
                move = Move(square, entry)
                new_game_state = add_move_to_game_state(game_state, move)
                children.append(new_game_state)
    
        return children
    
    def minimax(self, game_state: GameState, depth, alpha, beta, maximizingPlayer):
        if depth == 0:
            return self.evaluate(game_state)
        
        children = self.getChildren(game_state)

        if children is None:
            return self.evaluate(game_state)

        if maximizingPlayer:
            maxEval = -float('inf')
            for child in children:
                eval = self.minimax(child, depth-1, alpha, beta, False)
                maxEval = max(maxEval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return maxEval
        else:
            minEval = float('inf')
            for child in children:
                eval = self.minimax(child, depth-1, alpha, beta, True)
                minEval = min(minEval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return minEval
    
    def compute_best_move(self, game_state: GameState) -> None:
        # implementation based on naive_player, will propose moves with increasing depth
        valid_entries = ValidEntryFinder().get_pos_entries_boards(game_state.player_squares(), game_state.board)

        # Check whether a cell is empty, a value in that cell is not taboo, and that cell is allowed, this double checks some things
        def possible(i, j, value):
            return game_state.board.get((i, j)) == SudokuBoard.empty \
                   and not TabooMove((i, j), value) in game_state.taboo_moves \
                       and (i, j) in game_state.player_squares()

        all_moves = [Move((i, j), value) for (i, j) in valid_entries for value in valid_entries[(i, j)] if possible(i, j, value)]

        print(f'Number of possible moves: {len(all_moves)}')
        
        depth = 4
        alpha = -float('inf')
        beta = float('inf')

        while True:
            best_move = random.choice(all_moves)
            best_score = -float('inf')
            for move in all_moves:
                new_game_state = add_move_to_game_state(game_state, move)

                score = self.minimax(new_game_state, depth, alpha, beta, True)
                if score > best_score:
                    best_score = score
                    best_move = move
            self.propose_move(best_move)
            depth += 1
    
def add_move_to_game_state(game_state: GameState, move: Move):
    new_game_state = copy.deepcopy(game_state)
    new_game_state.board.put(move.square, move.value)
    new_game_state.moves.append(move)
    return new_game_state
    

class ValidEntryFinder:
    # TODO:
    # - make sure the allowed squares do not include filled in squares
    # - create valid __init__ (?)
    # - add doc strings and improve readability

    def __init__(self):
        pass

    def squares2values(self,squares : list, board) -> list:
        return [board.squares[board.square2index(sq)] for sq in squares]

    def get_pos_entries_row(self, allowed_squares, board, available_entries, game_state=None):
        dct = {}
        dct_pos_row_entries = {}

        # Get taboo moves for quick lookup if game_state exists
        taboo_moves = {}
        if game_state and game_state.taboo_moves:
            for move in game_state.taboo_moves:
                if move.square not in taboo_moves:
                    taboo_moves[move.square] = set()
                taboo_moves[move.square].add(move.value)

        # get possible entries per row present allowed_squares
        for square in allowed_squares:
            # get row coordinate
            row_coordinate = square[0]

            # check whether possible entries were already computed
            if row_coordinate not in dct:
                # get indices of entire row with row coordinate row_coordinate
                lst_row_coords = [(row_coordinate,i) for i in range(board.n*board.m)]

                # get current values of all items in the row (excluding 0/. as they are not valid entry options)
                row_values = self.squares2values(lst_row_coords,board)

                # get possible values for the current square based on rows
                dct[row_coordinate] = [val for val in available_entries if val not in row_values]
            
            # get the 
            dct_pos_row_entries[square] = dct[row_coordinate]

        return dct_pos_row_entries


    def get_pos_entries_col(self,allowed_squares,board,available_entries):
        dct = {}
        dct_pos_col_entries = {}

        # get possible entries per column present allowed_squares
        for square in allowed_squares:
            # get column coordinate
            col_coordinate = square[1]

            # check whether possible entries were already computed
            if col_coordinate not in dct:
                # get indices of entire column with column coordinate col_coordinate
                lst_col_coords = [(i,col_coordinate) for i in range(board.n*board.m)]
                # get current values of all items in the col (excluding 0/. as they are not valid entry options)
                col_values = self.squares2values(lst_col_coords,board)
                # get possible values for the current square based on columns
                dct[col_coordinate] = [val for val in available_entries if val not in col_values]
            
            # get the possible values from the column coordinate
            dct_pos_col_entries[square] = dct[col_coordinate]

        return dct_pos_col_entries


    def get_block_coords(self,coordinate,board) -> list:
        # nr rows & cols of entire board
        nr_rows = board.m
        nr_cols = board.n

        # nr cols & row per square
        nr_rows_per_square = board.n
        nr_cols_per_square = board.m

        # Identify the starting row and column of the square
        start_row = (coordinate[0] // nr_rows) * nr_rows
        start_col = (coordinate[1] // nr_cols) * nr_cols

        block_coords = [
            (r, c)
            for r in range(start_row, start_row + nr_cols_per_square)
            for c in range(start_col, start_col + nr_rows_per_square)
        ]

        return block_coords

    def get_pos_entries_block(self, allowed_squares, board, available_entries):
        dct_blocks = {}
        dct_pos_block_entries = {}
        
        for square in allowed_squares:
            # check whether already computed
            if all(str(square) not in block for block in dct_blocks):
                # get coordinates of the entire block in which the square is present
                lst_block_coords = self.get_block_coords(square,board)
            
                # get values inside these coordinates
                block_values = self.squares2values(lst_block_coords,board)

                # compute the possible entries
                pos_block_entries = [val for val in available_entries if val not in block_values]
                dct_pos_block_entries[square] = pos_block_entries
                dct_blocks[str(lst_block_coords)] = pos_block_entries
            else:
                # find correct key
                key = next((key for key in dct_blocks if str(square) in key), None)
                dct_pos_block_entries[square] = dct_blocks[key]

        return dct_pos_block_entries


    def get_pos_entries_boards(self, allowed_squares, board):
        available_entries = list(range(1, board.n*board.m+1))

        dct_pos_entries_row = self.get_pos_entries_row(allowed_squares, board, available_entries)
        dct_pos_entries_col = self.get_pos_entries_col(allowed_squares, board, available_entries)
        dct_pos_entries_block = self.get_pos_entries_block(allowed_squares, board, available_entries)

        dct_pos_entries = {}
        for square in dct_pos_entries_row:
            set_row = set(dct_pos_entries_row[square])
            set_col = set(dct_pos_entries_col[square])
            set_block = set(dct_pos_entries_block[square])

            dct_pos_entries[square] = set_row & set_col & set_block

        return dct_pos_entries