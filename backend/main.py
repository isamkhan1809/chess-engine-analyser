"""Chess Engine Analyser - FastAPI Backend."""

import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from chess_app.pgn_parser import parse_pgn
from chess_app.analyser import analyse_game
from chess_app.narrator import generate_narrative

load_dotenv()

app = FastAPI(
    title="Chess Engine Analyser",
    description="Analyse chess games from PGN files with AI-powered narrative.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PGNTextRequest(BaseModel):
    pgn_text: str


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "chess-engine-analyser"}


@app.post("/analyse")
async def analyse_game_endpoint(
    file: Optional[UploadFile] = File(default=None),
    pgn_text: Optional[str] = None,
):
    """
    Analyse a chess game from a PGN file upload or raw PGN text.

    Accepts:
    - Multipart file upload (file field)
    - JSON body {pgn_text: "..."}

    Returns full analysis: headers, moves with evals, turning points, blunders, accuracy, narrative.
    """
    raw_pgn = None

    # Try file upload first
    if file is not None:
        content = await file.read()
        try:
            raw_pgn = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_pgn = content.decode("latin-1")

    # Fall back to pgn_text form field
    elif pgn_text:
        raw_pgn = pgn_text

    if not raw_pgn or not raw_pgn.strip():
        raise HTTPException(status_code=400, detail="No PGN data provided. Upload a file or provide pgn_text.")

    # Parse PGN
    try:
        parsed = parse_pgn(raw_pgn)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PGN: {str(e)}")

    if not parsed["moves"]:
        raise HTTPException(status_code=422, detail="PGN contains no moves.")

    # Analyse game
    try:
        analysis = analyse_game(parsed["moves"], parsed["headers"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Generate narrative (optional - skip if no API key)
    narrative = None
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            narrative = generate_narrative(analysis, parsed["headers"])
        except Exception as e:
            # Narrative is optional; don't fail the whole request
            narrative = {
                "game_story": f"Narrative generation failed: {str(e)}",
                "key_moments": [],
                "winner_analysis": "",
                "loser_analysis": "",
                "improvement_tips": [],
                "opening_assessment": "",
            }
    else:
        narrative = {
            "game_story": "Set the ANTHROPIC_API_KEY environment variable to enable AI narrative generation.",
            "key_moments": [],
            "winner_analysis": "",
            "loser_analysis": "",
            "improvement_tips": ["Set ANTHROPIC_API_KEY to get AI-powered improvement tips."],
            "opening_assessment": "",
        }

    return {
        "headers": parsed["headers"],
        "total_moves": parsed["total_moves"],
        "result": parsed["result"],
        "moves": parsed["moves"],
        "move_evaluations": analysis["move_evaluations"],
        "turning_points": analysis["turning_points"],
        "blunders": analysis["blunders"],
        "mistakes": analysis["mistakes"],
        "white_accuracy": analysis["white_accuracy"],
        "black_accuracy": analysis["black_accuracy"],
        "opening_name": analysis["opening_name"],
        "narrative": narrative,
    }


@app.post("/analyse-text")
async def analyse_text_endpoint(request: PGNTextRequest):
    """Analyse a chess game from raw PGN text (JSON body)."""
    raw_pgn = request.pgn_text

    if not raw_pgn or not raw_pgn.strip():
        raise HTTPException(status_code=400, detail="pgn_text is empty.")

    try:
        parsed = parse_pgn(raw_pgn)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse PGN: {str(e)}")

    if not parsed["moves"]:
        raise HTTPException(status_code=422, detail="PGN contains no moves.")

    try:
        analysis = analyse_game(parsed["moves"], parsed["headers"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    narrative = None
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            narrative = generate_narrative(analysis, parsed["headers"])
        except Exception as e:
            narrative = {
                "game_story": f"Narrative generation failed: {str(e)}",
                "key_moments": [],
                "winner_analysis": "",
                "loser_analysis": "",
                "improvement_tips": [],
                "opening_assessment": "",
            }
    else:
        narrative = {
            "game_story": "Set the ANTHROPIC_API_KEY environment variable to enable AI narrative generation.",
            "key_moments": [],
            "winner_analysis": "",
            "loser_analysis": "",
            "improvement_tips": ["Set ANTHROPIC_API_KEY to get AI-powered improvement tips."],
            "opening_assessment": "",
        }

    return {
        "headers": parsed["headers"],
        "total_moves": parsed["total_moves"],
        "result": parsed["result"],
        "moves": parsed["moves"],
        "move_evaluations": analysis["move_evaluations"],
        "turning_points": analysis["turning_points"],
        "blunders": analysis["blunders"],
        "mistakes": analysis["mistakes"],
        "white_accuracy": analysis["white_accuracy"],
        "black_accuracy": analysis["black_accuracy"],
        "opening_name": analysis["opening_name"],
        "narrative": narrative,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
