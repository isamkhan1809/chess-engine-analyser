"""PGN Parser - Parse PGN files and extract moves with FEN positions."""

import io
import chess
import chess.pgn


def parse_pgn(pgn_text: str) -> dict:
    """
    Parse a PGN string and extract game data including headers, moves with FENs.

    Returns:
        dict with keys:
            - headers: dict (White, Black, Event, Date, Result, ECO, etc.)
            - moves: list of {move_number, san, uci, fen_before, fen_after, comment}
            - total_moves: int
            - result: str
    """
    pgn_io = io.StringIO(pgn_text.strip())
    game = chess.pgn.read_game(pgn_io)

    if game is None:
        raise ValueError("Could not parse PGN: no game found.")

    # Extract headers
    headers = {
        "White": game.headers.get("White", "Unknown"),
        "Black": game.headers.get("Black", "Unknown"),
        "Event": game.headers.get("Event", "Unknown Event"),
        "Date": game.headers.get("Date", "???"),
        "Result": game.headers.get("Result", "*"),
        "ECO": game.headers.get("ECO", ""),
        "Site": game.headers.get("Site", ""),
        "Round": game.headers.get("Round", ""),
        "WhiteElo": game.headers.get("WhiteElo", ""),
        "BlackElo": game.headers.get("BlackElo", ""),
    }

    board = game.board()
    moves = []
    move_number = 0

    for node in game.mainline():
        move = node.move
        fen_before = board.fen()
        san = board.san(move)
        uci = move.uci()

        # Determine move number (full move)
        full_move = board.fullmove_number
        color = "white" if board.turn == chess.WHITE else "black"

        board.push(move)
        fen_after = board.fen()

        comment = node.comment.strip() if node.comment else ""

        move_number += 1
        moves.append({
            "move_number": move_number,
            "full_move": full_move,
            "color": color,
            "san": san,
            "uci": uci,
            "fen_before": fen_before,
            "fen_after": fen_after,
            "comment": comment,
        })

    return {
        "headers": headers,
        "moves": moves,
        "total_moves": len(moves),
        "result": headers["Result"],
    }
