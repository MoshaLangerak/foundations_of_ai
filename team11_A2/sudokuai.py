#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

# import random
# import time
# import copy
# from competitive_sudoku.sudoku import TabooMove, SudokuBoard
from competitive_sudoku.sudoku import GameState, Move
import competitive_sudoku.sudokuai
from team11_A2.game_state_manager import GameStateManager
from team11_A2.valid_entry_finder import ValidEntryFinder
from team11_A2.heuristic_solver import HeuristicSolver

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
        
        moves = [[(i, j), value] for (i, j) in valid_entries for value in valid_entries[(i, j)]]

        solving_moves, potential_taboo_moves = HeuristicSolver(game_state).get_moves()
        
        if potential_taboo_moves != []:
            for move in potential_taboo_moves:
                if move in moves:
                    moves.remove(move)
        
        children = []
        for move in moves:
            move = Move(move[0], move[1])
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
                    # print('Pruning')
                    break
            return maxEval
        else:
            minEval = float('inf')
            for child in children:
                eval = self.minimax(child, depth-1, alpha, beta, True)
                minEval = min(minEval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    # print('Pruning')
                    break
            return minEval
    
    def compute_best_move(self, game_state: GameState) -> None:
        is_maximizing = self.player_number == 1

        valid_entries = ValidEntryFinder(game_state).get_pos_entries()
        moves = [[(i, j), value] for (i, j) in valid_entries for value in valid_entries[(i, j)]]

        # use the heuristic solver to get the solving and non-solving (taboo) moves
        solving_moves, potential_taboo_moves = HeuristicSolver(game_state).get_moves()

        # remove the non-solving moves from the list of valid moves
        if potential_taboo_moves != []:
            for move in potential_taboo_moves:
                if move in moves:
                    moves.remove(move)

        moves = [Move(square, value) for square, value in moves]
        
        # propose random move at the start of the game just in case depth 0 doesn't terminate
        self.propose_move(moves[len(moves)//2])

        current_stage = get_game_stage(len(moves))

        # set the maximum depth for iterative deepening
        max_depth = 15
        global_best_move = None
        global_best_score = -float('inf') if is_maximizing else float('inf')

        for depth in range(0, max_depth + 1):

            best_score = -float('inf') if is_maximizing else float('inf')
            best_move = None
            alpha = -float('inf')
            beta = float('inf')

            # first update the score of the global best move for the current depth
            if global_best_move is not None:
                new_game_state = GameStateManager().add_move_to_game_state(game_state, global_best_move)
                global_best_score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)

            # then check all possible moves for the current depth
            for i, move in enumerate(moves):
                new_game_state = GameStateManager().add_move_to_game_state(game_state, move)
                score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)

                if is_maximizing:
                    if score > best_score and not score == float('inf'):
                        best_score = score
                        best_move = move
                        
                        # if the score is better than the global best score (could be from a previous depth), update the global best move and propose it
                        if best_score > global_best_score:
                            global_best_score = best_score
                            global_best_move = best_move
                            self.propose_move(global_best_move)
                else:
                    if score < best_score and not score == float('-inf'):
                        best_score = score
                        best_move = move
                        
                        # if the score is better than the global best score (could be from a previous depth), update the global best move
                        if best_score < global_best_score:
                            global_best_score = best_score
                            global_best_move = best_move
                            self.propose_move(global_best_move)
            
            if potential_taboo_moves != [] and (current_stage == 'middle' or current_stage == 'late'):
                print(f'Checking taboo moves at depth {depth}')
                new_game_state = GameStateManager().add_potential_taboo_move_to_game_state(game_state, Move(potential_taboo_moves[0][0], potential_taboo_moves[0][1]))
                taboo_score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)
                print(f'Score for taboo move {potential_taboo_moves[0][0]} -> {potential_taboo_moves[0][1]} is {taboo_score}, best score is {best_score}')

                if is_maximizing:
                    if taboo_score > best_score:
                        best_score = taboo_score
                        best_move = potential_taboo_moves[0]
                else:
                    if taboo_score < best_score:
                        best_score = taboo_score
                        best_move = potential_taboo_moves[0]

            # only propose a move when all moves of the current depth have been checked <-- this is a design choice
            self.propose_move(best_move)
            global_best_move = best_move
            global_best_score = best_score


def get_game_stage(n_moves) -> str:
    """
    Determine the current game stage based on available moves.
    Args:
        n_moves: the number of available moves for given player
    Returns: 'early', 'middle', or 'late'
    """

    # thresholds to be adjusted based on testing
    if n_moves > 31: 
        return "early"
    elif n_moves <= 10:
        return "late"
    return "middle"
