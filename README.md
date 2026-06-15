<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=Chess%20Engine%20Analyser&fontSize=48&fontColor=fff&animation=fadeIn&desc=PGN%20Upload%20%7C%20Blunder%20Detection%20%7C%20Claude%20AI%20Narrative&descSize=18&descAlignY=75" width="100%" />

<br/>

<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=7C6AF7&center=true&vCenter=true&multiline=true&repeat=true&width=600&height=120&lines=Chess+Engine+Analyser;python-chess+%7C+Blunder+Detection;Turning+Points+%7C+Accuracy+Scores;Claude+AI+Narrative+%7C+Board+Visualisation" alt="Typing SVG" />
</a>

<br/><br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Anthropic](https://img.shields.io/badge/Claude-3.5%20Sonnet-D97706?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Features

- **📂 PGN Upload** — drag-and-drop or click-to-browse PGN file upload
- **🔍 Blunder Detection** — classifies every move: brilliant `!!`, good `✓`, inaccuracy `?!`, mistake `?`, blunder `??`
- **📈 Evaluation Chart** — interactive line chart of centipawn eval across all moves, colour-coded by classification
- **♛ Board Visualisation** — Unicode chess pieces on an 8×8 CSS grid, navigable move-by-move with Prev/Next/Jump controls
- **🎯 Accuracy Scores** — White vs Black percentage accuracy bars
- **🔴 Blunders Panel** — dedicated view of all blunders with before/after eval, click to jump to that board position
- **📖 Claude AI Narrative** — dramatic game story, key moments, winner/loser analysis, and improvement tips powered by `claude-3-5-sonnet-20241022`
- **⚡ Turning Points** — automatically detects the moves with the largest evaluation swings
- **🏆 Opening Assessment** — ECO code identification with Claude's narrative assessment

---

## 🗂️ Project Structure

```
chess-engine-analyser/
├── backend/
│   ├── main.py                  # FastAPI app — /analyse, /health endpoints
│   ├── chess_app/
│   │   ├── __init__.py
│   │   ├── pgn_parser.py        # PGN → moves with FEN snapshots
│   │   ├── analyser.py          # Material + positional heuristic eval
│   │   └── narrator.py          # Claude API narrative generation
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx              # Full React UI
│       └── App.css              # Dark-themed styles
├── sample.pgn                   # Anderssen's Immortal Game (1851)
└── README.md
```

---

## 🚀 Installation & Usage

### Prerequisites

- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### 1. Clone the repo

```bash
git clone https://github.com/isamkhan1809/chess-engine-analyser.git
cd chess-engine-analyser
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Start the backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the app

Visit **http://localhost:5173** and upload any `.pgn` file (try the included `sample.pgn`).

---

## 🔌 API Reference

### `POST /analyse`

Upload a PGN file for analysis.

**Request:** `multipart/form-data` with `file` field (`.pgn`)

**Response:**
```json
{
  "headers": { "White": "...", "Black": "...", "Result": "1-0", ... },
  "total_moves": 46,
  "move_evaluations": [
    {
      "move_number": 1, "san": "e4", "color": "white",
      "eval_before": 0, "eval_after": 15, "eval_delta": 15,
      "classification": "good"
    }
  ],
  "blunders": [...],
  "mistakes": [...],
  "turning_points": [...],
  "white_accuracy": 78.3,
  "black_accuracy": 61.5,
  "narrative": {
    "game_story": "...",
    "key_moments": [...],
    "winner_analysis": "...",
    "loser_analysis": "...",
    "improvement_tips": [...]
  }
}
```

### `POST /analyse-text`

Analyse from raw PGN text.

**Request:** `{ "pgn_text": "..." }`

### `GET /health`

Health check — returns `{ "status": "ok" }`.

---

## ⚙️ Move Classification

| Symbol | Class | Eval Delta |
|--------|-------|------------|
| `!!` | Brilliant | > +200 |
| `✓` | Good | -50 to +∞ |
| `?!` | Inaccuracy | -100 to -50 |
| `?` | Mistake | -200 to -100 |
| `??` | Blunder | < -200 |

Evaluations use material values (P=100, N=300, B=310, R=500, Q=900) plus piece-square table positional bonuses.

---

## 🧠 How Claude Narrates

The `narrator.py` module sends a structured prompt to `claude-3-5-sonnet-20241022` containing:
- Game metadata (players, result, ECO)
- All blunders and mistakes with eval context
- Key turning points
- Accuracy scores

Claude returns a JSON response with a dramatic game story, key moment descriptions, winner/loser analysis, and personalised improvement tips.

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" width="100%" />

Made with ♟ and Claude AI

</div>
