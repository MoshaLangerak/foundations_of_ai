from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove

from team11_A2.valid_entry_finder import ValidEntryFinder

class HeuristicSolver():

    def __init__(self, game_state: GameState) -> None:
        self.game_state = game_state
        self.valid_entries = ValidEntryFinder(game_state).get_pos_entries()

    def evaluate_entries(self):
        """
        Evaluates each valid entry based on heuristic rules to see if it is a taboo move or not.
        @return: list of taboo moves
        """

        