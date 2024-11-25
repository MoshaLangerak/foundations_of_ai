import subprocess
import argparse
import sys
import time
from typing import List, Dict
from collections import Counter
import os
import re
import psutil
from pathlib import Path


def run_game(game_id: int, game_args: List[str], output_file: str):
    """Run a single game in a new console window"""
    args_str = ' '.join(f'"{arg}"' for arg in game_args)
    window_title = f"Game {game_id}: {game_args[game_args.index('--first') + 1]} vs {game_args[game_args.index('--second') + 1]}"

    # Create a batch file with improved output handling
    batch_content = f"""
@echo off
title {window_title}
echo Starting {window_title}...
echo Game ID: {game_id} > "{output_file}"
echo First Player: {game_args[game_args.index('--first') + 1]} >> "{output_file}"
echo Second Player: {game_args[game_args.index('--second') + 1]} >> "{output_file}"
echo. >> "{output_file}"
python simulate_game.py {args_str} >> "{output_file}" 2>&1
set EXIT_CODE=%errorlevel%
echo. >> "{output_file}"
echo Exit Code: %EXIT_CODE% >> "{output_file}"
if %EXIT_CODE% neq 0 (
    echo GAME_STATUS: FAILED >> "{output_file}"
) else (
    echo GAME_STATUS: COMPLETED >> "{output_file}"
)
echo Game finished! > "{output_file}.status"
exit /b %EXIT_CODE%
"""

    batch_file = Path(f"run_game_{game_id}.bat")
    batch_file.write_text(batch_content, encoding='utf-8')

    # Launch the process with CREATE_NO_WINDOW flag and return a proper process object
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        process = subprocess.Popen(
            f'cmd /c "{batch_file}"',
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            shell=True
        )
        return process
    except Exception as e:
        print(f"Error starting game {game_id}: {e}")
        return None


def analyze_game_output(game_id: int, output_file: str, first_player: str, second_player: str) -> Dict:
    """Analyze a game's output file with improved parsing"""
    try:
        content = Path(output_file).read_text(encoding='utf-8')

        # More robust pattern matching
        moves_pattern = re.compile(
            r"Best move:|Player \d moves?|Move:|Selected move:", re.IGNORECASE)
        moves = len(moves_pattern.findall(content))

        # Improved winner detection
        winner = "Unknown"
        if re.search(r"Player 1 wins|Winner: *" + re.escape(first_player), content, re.IGNORECASE):
            winner = first_player
        elif re.search(r"Player 2 wins|Winner: *" + re.escape(second_player), content, re.IGNORECASE):
            winner = second_player
        elif re.search(r"Draw|Tie|Game is drawn", content, re.IGNORECASE):
            winner = "Draw"

        # Improved score detection
        score_matches = re.findall(
            r"(?:Score|Final score|Result): *(\d+)[^\d]+(\d+)", content, re.IGNORECASE)
        if score_matches:
            final_score = score_matches[-1]
            score = f"{final_score[0]}-{final_score[1]}"
        else:
            # Fallback score detection
            p1_score = len(re.findall(
                r"Player 1 captures|Player 1 wins", content, re.IGNORECASE))
            p2_score = len(re.findall(
                r"Player 2 captures|Player 2 wins", content, re.IGNORECASE))
            score = f"{p1_score}-{p2_score}"

        # Check if game completed successfully
        game_status = "Completed"
        if "GAME_STATUS: FAILED" in content:
            game_status = "Failed"

        return {
            "id": game_id,
            "winner": winner,
            "moves": moves,
            "score": score,
            "status": game_status
        }
    except Exception as e:
        print(f"Error analyzing game {game_id}: {str(e)}")
        return {
            "id": game_id,
            "winner": "Error",
            "moves": 0,
            "score": "0-0",
            "status": "Error"
        }


def wait_for_games(processes: List[subprocess.Popen], num_games: int, first_player: str, second_player: str) -> List[Dict]:
    """Wait for all games to complete with improved process handling"""
    results = []
    games_completed = set()
    active_processes = {i+1: p for i,
                        p in enumerate(processes) if p is not None}

    print("\nWaiting for games to complete...\n")

    timeout = 300  # 5 minutes timeout
    start_time = time.time()

    try:
        while len(games_completed) < num_games and (time.time() - start_time) < timeout:
            # Check each game's status
            for game_id, process in list(active_processes.items()):
                if game_id not in games_completed:
                    output_file = f"game_{game_id}_output.txt"
                    status_file = f"{output_file}.status"

                    # Check if process has finished
                    if process.poll() is not None:
                        if Path(status_file).exists():
                            try:
                                # Process the game results
                                result = analyze_game_output(
                                    game_id, output_file, first_player, second_player)
                                results.append(result)
                                games_completed.add(game_id)

                                status_str = "✓" if result['status'] == "Completed" else "✗"
                                print(
                                    f"Game {game_id} {status_str}: {result['winner']} won with score {result['score']} after {result['moves']} moves")

                                # Clean up process and remove from active processes
                                del active_processes[game_id]

                                # Clean up files
                                cleanup_game_files(game_id)
                            except Exception as e:
                                print(
                                    f"Warning: Error processing game {game_id}: {e}")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Cleaning up...")
    finally:
        # Clean up any remaining processes
        cleanup_processes(active_processes)

        # Clean up any remaining files
        for game_id in range(1, num_games + 1):
            cleanup_game_files(game_id)

    return results


def cleanup_game_files(game_id: int):
    """Clean up files associated with a game"""
    try:
        for file_pattern in [f"game_{game_id}_output.txt*", f"run_game_{game_id}.bat"]:
            for file_path in Path().glob(file_pattern):
                try:
                    file_path.unlink(missing_ok=True)
                except Exception as e:
                    print(f"Warning: Could not delete {file_path}: {e}")
    except Exception as e:
        print(f"Warning: Cleanup failed for game {game_id}: {e}")


def cleanup_processes(processes: Dict[int, subprocess.Popen]):
    """Clean up all running processes"""
    for game_id, process in processes.items():
        try:
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    # Wait up to 5 seconds for graceful termination
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()  # Force kill if process doesn't terminate
        except Exception as e:
            print(
                f"Warning: Could not terminate process for game {game_id}: {e}")


def print_summary(results: List[Dict]):
    if not results:
        print("\nNo games completed successfully.")
        return

    print("\nSummary:")
    # Count winners
    winner_counts = Counter(game["winner"] for game in results)
    total_games = len(results)

    # Print win percentages
    for winner, count in winner_counts.items():
        percentage = (count / total_games) * 100
        print(f"{winner}: {count} games ({percentage:.1f}%)")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run multiple games in parallel")
    parser.add_argument("--games", type=int, default=10,
                        help="Number of games to run")
    parser.add_argument("--first", required=True, help="First player")
    parser.add_argument("--second", required=True, help="Second player")
    parser.add_argument("--board", required=True, help="Board file")
    parser.add_argument("--time", type=float, default=1.0,
                        help="Time limit per move")

    args = parser.parse_args()

    game_args = [
        "--first", args.first,
        "--second", args.second,
        "--board", args.board,
        "--time", str(args.time)
    ]

    print(f"\nStarting {args.games} parallel games...")
    print(f"First player: {args.first}")
    print(f"Second player: {args.second}\n")

    # Launch games with a small delay between each
    processes = []
    for i in range(args.games):
        process = run_game(i + 1, game_args, f"game_{i+1}_output.txt")
        if process is not None:
            processes.append(process)
        time.sleep(0.5)

    # Wait for games to complete and analyze results
    results = wait_for_games(processes, args.games, args.first, args.second)

    # Print final summary
    print_summary(results)
