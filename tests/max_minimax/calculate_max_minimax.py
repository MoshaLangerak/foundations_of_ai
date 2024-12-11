from competitive_sudoku.sudoku import SudokuBoard, Move, TabooMove, GameState
from team11_A2.valid_entry_finder import ValidEntryFinder
from tests.max_minimax.utils import *
from pathlib import Path
import json, tempfile, os, re, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompetitiveSudoku:
    def __init__(self, board_size=2):
        self.board = SudokuBoard(board_size)
        self.scores = {1: 0, 2: 0}
        self.current_player = 1
        self.taboo_moves = []
        self.allowed_squares1, self.allowed_squares2 = self.generate_allowed_squares()
        self.occupied_squares1 = []
        self.occupied_squares2 = []

    def generate_allowed_squares(self):
        """Generates allowed squares for the game."""
        N = self.board.N
        return [(0, j) for j in range(N)], [(N - 1, j) for j in range(N)]

    def get_allowed_moves(self):
        """Get all allowed moves for the current player."""
        game_state = GameState(
            self.board,
            current_player=self.current_player,
            taboo_moves=self.taboo_moves,
            allowed_squares1=self.allowed_squares1,
            allowed_squares2=self.allowed_squares2,
            occupied_squares1=self.occupied_squares1,
            occupied_squares2=self.occupied_squares2
        )
        valid_entry_finder = ValidEntryFinder(game_state)
        pos_entries = valid_entry_finder.get_pos_entries()
        moves = []
        for square, values in pos_entries.items():
            for value in values:
                moves.append(Move(square=square, value=value))
        return moves

    def validate_with_oracle(self, move):
        """Check if the board remains solvable after a move using the Sudoku solver."""
        board_text = str(self.board)
        options = f"--move \"{move.square[0] * self.board.N + move.square[1]} {move.value}\""
        try:
            output = solve_sudoku(SUDOKU_SOLVER, board_text, options)
            if 'Invalid move' in output:
                return False, output, 'invalid'
            if 'Illegal move' in output:
                return False, output, 'illegal'
            if 'has no solution' in output:
                return False, output, 'no_solution'
            if 'The score is' in output:
                return True, output, 'valid'
            return False, output, 'unknown'
        except RuntimeError as e:
            logger.error(f"Error using Sudoku solver: {e}")
            return False, str(e), 'error'

    def make_move(self, move):
        """Make a move for the current player."""
        valid, output, status = self.validate_with_oracle(move)
        if not valid:
            if status == 'invalid':
                logger.warning(f"Invalid move: {move}. Player {3 - self.current_player} wins the game.")
                return False
            if status == 'illegal':
                logger.warning(f"Illegal move: {move}. Player {3 - self.current_player} wins the game.")
                return False
            if status == 'no_solution':
                logger.info(f"The sudoku has no solution after the move {move}.")
                self.taboo_moves.append(TabooMove(move.square, move.value))
                return False
            logger.error(f"Unknown error for move {move}: {output}")
            return False

        self.board.put(move.square, move.value)
        if self.current_player == 1:
            self.occupied_squares1.append(move.square)
        else:
            self.occupied_squares2.append(move.square)

        # Parse score from solve_sudoku output
        if 'The score is' in output:
            match = re.search(r'The score is ([-\d]+)', output)
            if match:
                score = int(match.group(1))
                self.scores[self.current_player] += score
            else:
                raise RuntimeError(f"Unexpected solver output: {output}")

        self.current_player = 3 - self.current_player  # Switch player
        return True

    def undo_move(self, move):
        """Undo the last move."""
        self.board.put(move.square, SudokuBoard.empty)
        if move.square in self.occupied_squares1:
            self.occupied_squares1.remove(move.square)
        else:
            self.occupied_squares2.remove(move.square)
        self.current_player = 3 - self.current_player  # Switch player back

    def is_game_over(self):
        """Check if the game is over."""
        return self.board.squares.count(SudokuBoard.empty) == 0

    def evaluate_board(self):
        """Evaluate the board score for minimax."""
        board_text = str(self.board)
        options = ''
        try:
            output = solve_sudoku(SUDOKU_SOLVER, board_text, options)
            if 'The score is' in output:
                match = re.search(r'The score is ([-\d]+)', output)
                if match:
                    return int(match.group(1))
            return 0
        except RuntimeError as e:
            logger.error(f"Error evaluating board: {e}")
            return 0

def solve_sudoku(solve_sudoku_path: str, board_text: str, options: str = '') -> str:
    """
    Execute the solve_sudoku program.
    @param solve_sudoku_path: The location of the solve_sudoku executable.
    @param board_text: A string representation of a sudoku board.
    @param options: Additional command line options.
    @return: The output of solve_sudoku.
    """
    if not os.path.exists(solve_sudoku_path):
        raise RuntimeError(
            f'No oracle found at location "{solve_sudoku_path}"')
    filename = tempfile.NamedTemporaryFile(prefix='solve_sudoku_').name
    Path(filename).write_text(board_text)
    command = f'{solve_sudoku_path} {filename} {options}'
    return execute_command(command)

def minimax_with_tree(game, depth, maximizing_player, tree_node=None, stats=None, alpha=float('-inf'), beta=float('inf')):
    """Minimax algorithm with alpha-beta pruning, tree construction, and logging."""
    if stats is None:
        stats = {"branches": 0, "base_cases": 0}

    if depth == 0 or game.is_game_over():
        stats["base_cases"] += 1
        logger.info(f"Base case reached. Total base cases: {stats['base_cases']}")
        score = game.evaluate_board()
        if tree_node:
            tree_node.score = score
        return score

    allowed_moves = game.get_allowed_moves()
    if not allowed_moves:
        stats["base_cases"] += 1
        logger.info(f"Base case (no moves) reached. Total base cases: {stats['base_cases']}")
        score = game.evaluate_board()
        if tree_node:
            tree_node.score = score
        return score

    stats["branches"] += 1
    logger.info(f"Branching at depth {depth}. Total branches: {stats['branches']}")

    if maximizing_player:
        max_eval = float('-inf')
        for move in allowed_moves:
            if game.make_move(move):
                child_node = TreeNode(move=move)
                if tree_node:
                    tree_node.children.append(child_node)
                eval = minimax_with_tree(game, depth - 1, False, child_node, stats, alpha, beta)
                game.undo_move(move)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    logger.info("Pruning branches in maximizing player.")
                    break
        if tree_node:
            tree_node.score = max_eval
        return max_eval
    else:
        min_eval = float('inf')
        for move in allowed_moves:
            if game.make_move(move):
                child_node = TreeNode(move=move)
                if tree_node:
                    tree_node.children.append(child_node)
                eval = minimax_with_tree(game, depth - 1, True, child_node, stats, alpha, beta)
                game.undo_move(move)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    logger.info("Pruning branches in minimizing player.")
                    break
        if tree_node:
            tree_node.score = min_eval
        return min_eval

if __name__ == "__main__":
    game = CompetitiveSudoku()
    depth = float('inf')
    best_score = float('-inf')
    best_move = None
    game_tree = TreeNode(move=None)  # Root node for the game tree

    stats = {"branches": 0, "base_cases": 0}

    for move in game.get_allowed_moves():
        if game.make_move(move):
            child_node = TreeNode(move=move)
            game_tree.children.append(child_node)
            score = minimax_with_tree(game, depth - 1, False, child_node, stats)
            game.undo_move(move)
            if score > best_score:
                best_score = score
                best_move = move

    logger.info(f"Best move for player 1: {best_move} with score {best_score}")
    logger.info(f"Total branches explored: {stats['branches']}")
    logger.info(f"Total base cases reached: {stats['base_cases']}")

    # Save the tree as a JSON file
    with open("game_tree.json", "w") as f:
        json.dump(game_tree.to_dict(), f, indent=4)
