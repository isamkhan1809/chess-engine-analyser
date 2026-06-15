"""Chess Analyser - Evaluate positions using heuristics and classify moves."""

import chess
from typing import List, Dict, Any

# Material values in centipawns
MATERIAL_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 310,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Piece-square tables for positional bonuses (from white's perspective)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MIDDLE_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PIECE_TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_MIDDLE_TABLE,
}


def evaluate_position(board: chess.Board) -> int:
    """
    Evaluate a chess position using material count and basic positional heuristics.
    Returns centipawn score: positive = white advantage, negative = black advantage.
    """
    if board.is_checkmate():
        # The side to move is in checkmate (they lost)
        return -30000 if board.turn == chess.WHITE else 30000

    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0

    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        table = PIECE_TABLES[piece_type]
        material = MATERIAL_VALUES[piece_type]

        # White pieces
        for sq in board.pieces(piece_type, chess.WHITE):
            # For white, index normally (a1=0 -> h8=63, but display is flipped)
            table_idx = sq  # a1=0, h8=63
            score += material + table[table_idx]

        # Black pieces (mirror the table)
        for sq in board.pieces(piece_type, chess.BLACK):
            # Mirror vertically for black
            mirrored = chess.square_mirror(sq)
            score -= material + table[mirrored]

    # Mobility bonus (number of legal moves)
    current_turn = board.turn
    mobility_score = len(list(board.legal_moves)) * 5

    if current_turn == chess.WHITE:
        score += mobility_score
    else:
        score -= mobility_score

    return score


def classify_move(eval_delta: int, player_color: str) -> str:
    """
    Classify a move based on evaluation change from the player's perspective.
    eval_delta: positive means the player improved their position, negative means they worsened it.
    """
    # From player's perspective: negative delta = bad move
    if eval_delta > 200:
        return "brilliant"
    elif eval_delta >= -50:
        return "good"
    elif eval_delta >= -100:
        return "inaccuracy"
    elif eval_delta >= -200:
        return "mistake"
    else:
        return "blunder"


def analyse_game(moves: List[Dict], headers: Dict) -> Dict[str, Any]:
    """
    Analyse all moves in the game, computing evaluations and classifications.

    Returns dict with:
        - move_evaluations: list of evaluated moves
        - turning_points: significant eval shifts
        - blunders: list of blunder moves
        - mistakes: list of mistake moves
        - white_accuracy: float percentage
        - black_accuracy: float percentage
        - opening_name: str
    """
    move_evaluations = []
    blunders = []
    mistakes = []
    turning_points = []

    prev_eval = 0  # Start from equal position

    for move_data in moves:
        fen_before = move_data["fen_before"]
        fen_after = move_data["fen_after"]
        color = move_data["color"]

        board_before = chess.Board(fen_before)
        board_after = chess.Board(fen_after)

        eval_before = evaluate_position(board_before)
        eval_after = evaluate_position(board_after)

        # From player's perspective:
        # White wants positive evals. If white played and eval went from +50 to -100, delta = -150 (bad for white)
        # Black wants negative evals. If black played and eval went from +50 to -100, delta = +150 (good for black)
        if color == "white":
            eval_delta = eval_after - eval_before
        else:
            eval_delta = eval_before - eval_after  # black benefits when eval decreases

        classification = classify_move(eval_delta, color)

        entry = {
            "move_number": move_data["move_number"],
            "full_move": move_data["full_move"],
            "color": color,
            "san": move_data["san"],
            "uci": move_data["uci"],
            "fen_before": fen_before,
            "fen_after": fen_after,
            "eval_before": eval_before,
            "eval_after": eval_after,
            "eval_delta": eval_delta,
            "classification": classification,
        }

        move_evaluations.append(entry)

        if classification == "blunder":
            blunders.append(entry)
        elif classification == "mistake":
            mistakes.append(entry)

        # Turning points: large eval shifts in either direction
        if abs(eval_after - eval_before) > 150:
            turning_points.append(entry)

        prev_eval = eval_after

    # Calculate accuracy
    white_moves = [m for m in move_evaluations if m["color"] == "white"]
    black_moves = [m for m in move_evaluations if m["color"] == "black"]

    def calc_accuracy(player_moves):
        if not player_moves:
            return 100.0
        good_moves = sum(
            1 for m in player_moves
            if m["classification"] in ("brilliant", "good", "inaccuracy")
        )
        return round(good_moves / len(player_moves) * 100, 1)

    white_accuracy = calc_accuracy(white_moves)
    black_accuracy = calc_accuracy(black_moves)

    # Opening name from ECO or default
    eco = headers.get("ECO", "")
    opening_name = f"ECO {eco}" if eco else "Unknown Opening"

    return {
        "move_evaluations": move_evaluations,
        "turning_points": turning_points,
        "blunders": blunders,
        "mistakes": mistakes,
        "white_accuracy": white_accuracy,
        "black_accuracy": black_accuracy,
        "opening_name": opening_name,
    }
