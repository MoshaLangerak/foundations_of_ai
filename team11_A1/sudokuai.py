#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, game_state: GameState):
        return None
    
    def getChildren(self, game_state: GameState):
        return None
    
    def minimax(self, game_state: GameState, depth, maximizingPlayer):
        return None
    
    def compute_best_move(self, game_state: GameState) -> None:
        return None