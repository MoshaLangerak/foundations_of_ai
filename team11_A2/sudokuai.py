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
        # implementation based on naive_player, will propose moves with increasing depth
        valid_entries = ValidEntryFinder(game_state).get_pos_entries()
        moves = [Move((i, j), value) for (i, j) in valid_entries for value in valid_entries[(i, j)]] # ! This could be moved into the entryfinder class
        
        # propose random move at the start of the game just in case depth 0 doesn't terminate
        self.propose_move(moves[len(moves)//2])

        current_stage = get_game_stage(len(moves))
        print("--------------- Available moves: ", len(moves), " --------------- ")
        print(f"\n\n\nCurrent game stage: {current_stage}")

        is_maximizing = self.player_number == 1

        # print(f'Player {self.player_number} is maximizing: {is_maximizing}')
        # print("Played taboo moves: ", ", ".join(str(move) for move in game_state.taboo_moves), "\n")

        # set the maximum depth for iterative deepening
        max_depth = 15
        global_best_move = None
        global_best_score = -float('inf') if is_maximizing else float('inf')

        for depth in range(0, max_depth + 1):
            print(f'-------- Checking depth {depth} --------')

            best_score = -float('inf') if is_maximizing else float('inf')
            best_move = None
            alpha = -float('inf')
            beta = float('inf')

            # first update the score of the global best move for the current depth
            if global_best_move is not None:
                new_game_state = GameStateManager().add_move_to_game_state(game_state, global_best_move)
                global_best_score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)
                # print(f'Global best move {global_best_move.square} -> {global_best_move.value} has score {global_best_score} at depth {depth}')

            # then check all possible moves for the current depth
            for i, move in enumerate(moves):
                # print(f'Checking move {i}: {move.square} -> {move.value}')
                new_game_state = GameStateManager().add_move_to_game_state(game_state, move)
                score = self.minimax(new_game_state, depth, alpha, beta, is_maximizing)

                # print(f'Score for move {move.square} -> {move.value} is {score}, best score is {best_score}{" (inf/-inf expected)" if i == 0 else ""}')

                if is_maximizing:
                    if score > best_score and not score == float('inf'):
                        best_score = score
                        best_move = move
                        # print(f'New best move: {best_move.square} -> {best_move.value} with score {best_score}')
                        
                        # if the score is better than the global best score (could be from a previous depth), update the global best move and propose it
                        if best_score > global_best_score:
                            global_best_score = best_score
                            global_best_move = best_move
                            self.propose_move(global_best_move)
                            # print(f'Move is also global best move, so proposed: {global_best_move.square} -> {global_best_move.value} with score {global_best_score}')
                else:
                    if score < best_score and not score == float('-inf'):
                        best_score = score
                        best_move = move
                        # print(f'New best move: {best_move.square} -> {best_move.value} with score {best_score}')
                        
                        # if the score is better than the global best score (could be from a previous depth), update the global best move
                        if best_score < global_best_score:
                            global_best_score = best_score
                            global_best_move = best_move
                            self.propose_move(global_best_move)
                            # print(f'Move is also global best move, so proposed: {global_best_move.square} -> {global_best_move.value} with score {global_best_score}')
            
            # only propose a move when all moves of the current depth have been checked <-- this is a design choice
            self.propose_move(best_move)
            global_best_move = best_move
            global_best_score = best_score
            # print(f'Best move proposed: {best_move.square} -> {best_move.value} with score {best_score}')


def get_game_stage(n_moves) -> str:
    """
    Determine the current game stage based on number of empty squares.
    Args:
        n_moves: the number of available moves for given player
    Returns: 'early', 'middle', or 'late'
    """

    # thresholds can be adjusted based on testing
    if n_moves > 31: 
        return "early"
    elif n_moves <= 10:
        return "late"
    return "middle"  # Here it usually checks for depth 0/1 sometimes 2/3
