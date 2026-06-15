"""Narrator - Generate Claude AI narrative analysis of the chess game."""

import os
import anthropic
from typing import Dict, Any, List


def generate_narrative(game_analysis: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Use Claude to generate a dramatic narrative analysis of the chess game.

    Returns dict with:
        - game_story: str (dramatic narrative)
        - key_moments: list of {move_number, description, significance}
        - winner_analysis: str
        - loser_analysis: str
        - improvement_tips: list[str]
        - opening_assessment: str
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)

    white = headers.get("White", "White")
    black = headers.get("Black", "Black")
    result = headers.get("Result", "*")
    event = headers.get("Event", "Unknown Event")
    opening = game_analysis.get("opening_name", "Unknown Opening")
    white_acc = game_analysis.get("white_accuracy", 0)
    black_acc = game_analysis.get("black_accuracy", 0)

    # Determine winner
    if result == "1-0":
        winner, loser = white, black
    elif result == "0-1":
        winner, loser = black, white
    else:
        winner, loser = None, None

    # Build move summary for context
    blunders = game_analysis.get("blunders", [])
    mistakes = game_analysis.get("mistakes", [])
    turning_points = game_analysis.get("turning_points", [])
    move_evaluations = game_analysis.get("move_evaluations", [])

    blunder_summary = "\n".join([
        f"- Move {b['move_number']} ({b['color'].title()}): {b['san']} "
        f"(eval went from {b['eval_before']} to {b['eval_after']}, delta {b['eval_delta']})"
        for b in blunders[:10]
    ]) or "None"

    turning_point_summary = "\n".join([
        f"- Move {t['move_number']} ({t['color'].title()}): {t['san']} "
        f"(eval shift: {t['eval_before']} → {t['eval_after']})"
        for t in turning_points[:8]
    ]) or "None"

    mistake_summary = "\n".join([
        f"- Move {m['move_number']} ({m['color'].title()}): {m['san']} "
        f"(eval delta {m['eval_delta']})"
        for m in mistakes[:10]
    ]) or "None"

    total_moves = len(move_evaluations)

    prompt = f"""You are an expert chess commentator and coach. Analyse the following chess game and provide a detailed, engaging narrative.

GAME DETAILS:
- Event: {event}
- White: {white} (Accuracy: {white_acc}%)
- Black: {black} (Accuracy: {black_acc}%)
- Result: {result}
- Opening: {opening}
- Total half-moves: {total_moves}
- Winner: {winner if winner else "Draw"}

BLUNDERS (severe mistakes):
{blunder_summary}

MISTAKES:
{mistake_summary}

KEY TURNING POINTS (large evaluation shifts):
{turning_point_summary}

Please provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
  "game_story": "A dramatic 3-4 paragraph narrative of how the game unfolded, the key moments, and the decisive factor. Write as if commentating for an audience.",
  "key_moments": [
    {{
      "move_number": <int>,
      "description": "<what happened and why it was significant>",
      "significance": "<high|medium|critical>"
    }}
  ],
  "winner_analysis": "2-3 sentences on why {winner if winner else 'this result'} was achieved - what they did well.",
  "loser_analysis": "2-3 sentences on what went wrong for {loser if loser else 'the other player'} - specific errors.",
  "improvement_tips": [
    "Tip 1 for the losing side",
    "Tip 2",
    "Tip 3",
    "Tip 4",
    "Tip 5"
  ],
  "opening_assessment": "Brief assessment of how the opening was handled by both sides."
}}"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text.strip()

    # Parse JSON response
    import json
    # Handle possible markdown code fences
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first and last lines if they're code fences
        lines = [l for l in lines if not l.startswith("```")]
        response_text = "\n".join(lines)

    try:
        narrative_data = json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        narrative_data = {
            "game_story": response_text,
            "key_moments": [],
            "winner_analysis": f"{winner} played well to secure the win." if winner else "The game ended in a draw.",
            "loser_analysis": f"{loser} made some critical errors." if loser else "Both sides played evenly.",
            "improvement_tips": [
                "Review your blunders and understand why they were mistakes.",
                "Study the opening you played to understand the key ideas.",
                "Practice tactical puzzles to improve your calculation.",
                "Analyse your games regularly to identify patterns in your mistakes.",
                "Focus on piece activity and king safety in the middlegame.",
            ],
            "opening_assessment": f"The game opened with {opening}.",
        }

    return narrative_data
