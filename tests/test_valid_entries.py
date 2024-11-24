from team11_A1.sudokuai import ValidEntryFinder
from test_classes import GameState, TabooMove, SudokuBoard

# Looking at values only, ignoring player ownership for simplicity

def create_test_board_2x2():
    board = SudokuBoard(2, 2)

    values = [
        [0, 1, 0, 2],
        [2, 0, 3, 0],
        [4, 2, 0, 0],
        [1, 0, 2, 4]
    ]

    for i in range(4):
        for j in range(4):
            if values[i][j] != 0:
                board.put((i, j), values[i][j])

    taboo_moves = [TabooMove((2, 3), 1)]

    game_state = GameState(board, taboo_moves)

    # Squares where moves are allowed
    game_state._player_squares = [(0, 0), (0, 2), (1, 1), (1, 3), (2, 2), (2, 3), (3, 1)]

    # Expected valid entries for each allowed position
    expected_results = {
        (0, 0): {3},
        (0, 2): {4},
        (1, 1): {4},
        (1, 3): {1},
        (2, 2): {1},
        (2, 3): {3},  # also 1 but 1 is taboo
        (3, 1): {3}
    }

    return game_state, "2x2 Board Test", expected_results


def run_tests(test_boards):
    """Run test cases and report results"""
    total = len(test_boards)
    passed = 0

    for i, board_creator in enumerate(test_boards, 1):
        game_state, test_name, expected = board_creator()
        print(f"\n=== Running Test {i}: {test_name} ===")

        finder = ValidEntryFinder(game_state)
        actual = finder.get_pos_entries()

        print("Your class found these values:")
        print(actual)

        # Compare results
        missing = {
            pos: values - actual.get(pos, set())
            for pos, values in expected.items()
            if pos not in actual or values - actual[pos]
        }

        extra = {
            pos: values - expected.get(pos, set())
            for pos, values in actual.items()
            if pos not in expected or values - expected.get(pos, set())
        }

        # Print results
        if not missing and not extra:
            print("✅")
            passed += 1
        else:
            if missing:
                print("❌ Missing:", missing)
            if extra:
                print("❌ Extra:", extra)

        print("\nFound:")
        for pos in sorted(actual.keys()):
            print(f"  {pos}: {sorted(list(actual[pos]))}")

    print(f"\n=== Test Summary ===")
    print(f"Passed: {passed}/{total} tests")


if __name__ == "__main__":
    run_tests([create_test_board_2x2])
