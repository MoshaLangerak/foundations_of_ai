import subprocess, tempfile, platform, os
from pathlib import Path

SUDOKU_SOLVER = 'bin\\solve_sudoku.exe' if platform.system() == 'Windows' else 'bin/solve_sudoku'


def execute_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        output = result.stdout or result.stderr
    except Exception as e:
        output = str(e)
    return output.strip()


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


class TreeNode:
    def __init__(self, move=None, score=None):
        self.move = move  # The move leading to this node
        self.score = score  # The evaluation score for this node
        self.children = []  # List of child nodes

    def to_dict(self):
        """Convert the tree node to a dictionary for JSON export."""
        return {
            "move": str(self.move) if self.move else None,
            "score": self.score,
            "children": [child.to_dict() for child in self.children]
        }
