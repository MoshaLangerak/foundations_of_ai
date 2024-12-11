import copy

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove

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