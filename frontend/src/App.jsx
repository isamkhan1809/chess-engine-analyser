import { useState, useCallback, useRef, useEffect } from 'react'
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

// ===== FEN Parser =====
const PIECE_UNICODE = {
  K: '♔', Q: '♕', R: '♖', B: '♗', N: '♘', P: '♙',
  k: '♚', q: '♛', r: '♜', b: '♝', n: '♞', p: '♟',
}

function parseFEN(fen) {
  const board = Array(8).fill(null).map(() => Array(8).fill(null))
  const parts = fen.split(' ')
  const rows = parts[0].split('/')
  rows.forEach((row, rankIdx) => {
    let fileIdx = 0
    for (const ch of row) {
      if (/\d/.test(ch)) {
        fileIdx += parseInt(ch)
      } else {
        board[rankIdx][fileIdx] = ch
        fileIdx++
      }
    }
  })
  return board
}

// ===== Chessboard Component =====
function Chessboard({ fen, highlightSquares = [] }) {
  const board = parseFEN(fen)
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

  return (
    <div className="chess-board">
      {board.map((row, rankIdx) =>
        row.map((piece, fileIdx) => {
          const isLight = (rankIdx + fileIdx) % 2 === 0
          const squareName = files[fileIdx] + (8 - rankIdx)
          const isHighlighted = highlightSquares.includes(squareName)
          return (
            <div
              key={`${rankIdx}-${fileIdx}`}
              className={`chess-square ${isLight ? 'light' : 'dark'} ${isHighlighted ? 'highlighted' : ''}`}
            >
              {rankIdx === 7 && <span className="coord file">{files[fileIdx]}</span>}
              {fileIdx === 0 && <span className="coord rank">{8 - rankIdx}</span>}
              {piece && (
                <span className="piece" role="img" aria-label={piece}>
                  {PIECE_UNICODE[piece] || ''}
                </span>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}

// ===== Classification Pill =====
function ClassPill({ cls }) {
  return (
    <span className={`classification-pill pill-${cls}`}>
      {cls === 'inaccuracy' ? '?!' : cls === 'mistake' ? '?' : cls === 'blunder' ? '??' : cls === 'brilliant' ? '!!' : '✓'}
      {' '}{cls}
    </span>
  )
}

// ===== Eval Chip =====
function EvalChip({ value }) {
  const v = Math.round(value)
  const cls = v > 0 ? 'positive' : v < 0 ? 'negative' : ''
  const display = v > 0 ? `+${v}` : `${v}`
  return <span className={`eval-chip ${cls}`}>{display}</span>
}

// ===== Eval Chart =====
function EvalChart({ moveEvals }) {
  const labels = moveEvals.map((m) => {
    const prefix = m.color === 'white' ? '' : '…'
    return `${m.full_move}${prefix} ${m.san}`
  })
  const data = {
    labels,
    datasets: [
      {
        label: 'Eval (centipawns)',
        data: moveEvals.map((m) => Math.max(-1500, Math.min(1500, m.eval_after))),
        borderColor: '#7c6af7',
        backgroundColor: (ctx) => {
          const chart = ctx.chart
          const { chartArea } = chart
          if (!chartArea) return 'transparent'
          const gradient = chart.ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
          gradient.addColorStop(0, 'rgba(124,106,247,0.35)')
          gradient.addColorStop(0.5, 'rgba(124,106,247,0.05)')
          gradient.addColorStop(1, 'rgba(248,113,113,0.15)')
          return gradient
        },
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 5,
        pointBackgroundColor: (ctx) => {
          const m = moveEvals[ctx.dataIndex]
          if (!m) return '#7c6af7'
          if (m.classification === 'blunder') return '#f87171'
          if (m.classification === 'mistake') return '#fb923c'
          if (m.classification === 'inaccuracy') return '#facc15'
          if (m.classification === 'brilliant') return '#60a5fa'
          return '#7c6af7'
        },
        borderWidth: 2,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e2235',
        borderColor: '#2d3154',
        borderWidth: 1,
        titleColor: '#e8eaf6',
        bodyColor: '#8892b0',
        callbacks: {
          label: (ctx) => {
            const m = moveEvals[ctx.dataIndex]
            const val = ctx.parsed.y
            return [
              `Eval: ${val > 0 ? '+' : ''}${val}`,
              `Classification: ${m?.classification || ''}`,
            ]
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#4a5568', font: { size: 10 }, maxRotation: 45 },
        grid: { color: 'rgba(45,49,84,0.4)' },
      },
      y: {
        ticks: {
          color: '#4a5568',
          font: { size: 10 },
          callback: (v) => (v > 0 ? `+${v}` : v),
        },
        grid: { color: 'rgba(45,49,84,0.4)' },
        min: -1500,
        max: 1500,
      },
    },
  }

  return (
    <div className="chart-wrapper">
      <Line data={data} options={options} />
    </div>
  )
}

// ===== Main App =====
export default function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [currentMoveIdx, setCurrentMoveIdx] = useState(0)
  const activeRowRef = useRef(null)

  const INITIAL_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

  const handleFile = (f) => {
    if (f && (f.name.endsWith('.pgn') || f.type === 'text/plain')) {
      setFile(f)
      setError(null)
    } else {
      setError('Please upload a valid .pgn file.')
    }
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    handleFile(f)
  }, [])

  const handleSubmit = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    setCurrentMoveIdx(0)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await axios.post('/analyse', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Analysis failed.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setCurrentMoveIdx(0)
  }

  // Scroll active move row into view
  useEffect(() => {
    if (activeRowRef.current) {
      activeRowRef.current.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [currentMoveIdx])

  const moveEvals = result?.move_evaluations || []
  const currentMoveData = moveEvals[currentMoveIdx] || null

  const currentFen = currentMoveIdx === 0
    ? (result?.moves?.[0]?.fen_before || INITIAL_FEN)
    : (moveEvals[currentMoveIdx - 1]?.fen_after || INITIAL_FEN)

  // Parse UCI to get highlight squares
  const highlightSquares = []
  if (currentMoveData?.uci && currentMoveIdx > 0) {
    const uci = moveEvals[currentMoveIdx - 1]?.uci || ''
    if (uci.length >= 4) {
      highlightSquares.push(uci.slice(0, 2), uci.slice(2, 4))
    }
  }

  const narrative = result?.narrative || {}

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <span className="header-icon">♟</span>
        <h1>Chess Engine Analyser</h1>
        <p>Upload a PGN file · Detect blunders · Get Claude AI narrative</p>
      </header>

      {/* Upload Section */}
      {!result && !loading && (
        <div className="upload-section">
          <div
            className={`upload-zone ${dragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              type="file"
              accept=".pgn,.txt"
              onChange={(e) => handleFile(e.target.files[0])}
            />
            <span className="upload-icon">📂</span>
            <h3>Drop your PGN file here</h3>
            <p>or click to browse · .pgn files only</p>
            {file && <div className="file-name">📄 {file.name}</div>}
          </div>

          {error && <div className="error-banner">⚠ {error}</div>}

          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={!file}
          >
            ♟ Analyse Game
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading-overlay">
          <div className="spinner" />
          <h3>Analysing your game…</h3>
          <p>Parsing moves, evaluating positions, generating AI narrative</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="results">

          {/* Game Info Header */}
          <div className="game-info-header">
            <div className="game-players">
              <div className="player-block">
                <div className="player-color-dot white" />
                <div className="player-name">{result.headers.White}</div>
                {result.headers.WhiteElo && (
                  <div className="player-elo">ELO {result.headers.WhiteElo}</div>
                )}
              </div>
              <div>
                <div className="vs-badge">vs</div>
                <div className="result-badge">{result.result}</div>
              </div>
              <div className="player-block">
                <div className="player-color-dot black" />
                <div className="player-name">{result.headers.Black}</div>
                {result.headers.BlackElo && (
                  <div className="player-elo">ELO {result.headers.BlackElo}</div>
                )}
              </div>
            </div>
            <div className="game-meta">
              <span>🏆 {result.headers.Event}</span>
              <span>📅 {result.headers.Date}</span>
              {result.headers.Site && <span>📍 {result.headers.Site}</span>}
              <span>♟ {result.opening_name}</span>
              <span>🔢 {result.total_moves} half-moves</span>
            </div>
          </div>

          {/* Accuracy Cards */}
          <div className="accuracy-row">
            <div className="accuracy-card white-card">
              <div className="accuracy-label">White Accuracy</div>
              <div className="accuracy-player">{result.headers.White}</div>
              <div className="accuracy-value">{result.white_accuracy}%</div>
              <div className="accuracy-bar">
                <div className="accuracy-bar-fill" style={{ width: `${result.white_accuracy}%` }} />
              </div>
            </div>
            <div className="accuracy-card black-card">
              <div className="accuracy-label">Black Accuracy</div>
              <div className="accuracy-player">{result.headers.Black}</div>
              <div className="accuracy-value">{result.black_accuracy}%</div>
              <div className="accuracy-bar">
                <div className="accuracy-bar-fill" style={{ width: `${result.black_accuracy}%` }} />
              </div>
            </div>
          </div>

          {/* Evaluation Chart */}
          <div className="card">
            <div className="section-title">
              <span className="icon">📈</span> Evaluation Over Time
            </div>
            <EvalChart moveEvals={moveEvals} />
          </div>

          {/* Board + Move List */}
          <div className="card">
            <div className="section-title">
              <span className="icon">♛</span> Board &amp; Move Explorer
            </div>
            <div className="board-moves-layout">
              {/* Board */}
              <div className="board-container">
                <Chessboard fen={currentFen} highlightSquares={highlightSquares} />
                <div className="board-nav">
                  <button className="nav-btn" onClick={() => setCurrentMoveIdx(0)} disabled={currentMoveIdx === 0}>⏮</button>
                  <button className="nav-btn" onClick={() => setCurrentMoveIdx(i => Math.max(0, i - 1))} disabled={currentMoveIdx === 0}>◀</button>
                  <span className="move-indicator">
                    {currentMoveIdx === 0 ? 'Start' : `Move ${currentMoveIdx}/${moveEvals.length}`}
                  </span>
                  <button className="nav-btn" onClick={() => setCurrentMoveIdx(i => Math.min(moveEvals.length, i + 1))} disabled={currentMoveIdx === moveEvals.length}>▶</button>
                  <button className="nav-btn" onClick={() => setCurrentMoveIdx(moveEvals.length)} disabled={currentMoveIdx === moveEvals.length}>⏭</button>
                </div>
                {currentMoveIdx > 0 && moveEvals[currentMoveIdx - 1] && (
                  <div className="board-move-san">
                    {moveEvals[currentMoveIdx - 1].full_move}.
                    {moveEvals[currentMoveIdx - 1].color === 'black' ? '..' : ''}{' '}
                    {moveEvals[currentMoveIdx - 1].san}
                    {' '}
                    <ClassPill cls={moveEvals[currentMoveIdx - 1].classification} />
                  </div>
                )}
              </div>

              {/* Move List */}
              <div className="move-list-container">
                <table className="move-list-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Move</th>
                      <th>Classification</th>
                      <th>Eval</th>
                    </tr>
                  </thead>
                  <tbody>
                    {moveEvals.map((m, idx) => (
                      <tr
                        key={idx}
                        ref={idx + 1 === currentMoveIdx ? activeRowRef : null}
                        className={idx + 1 === currentMoveIdx ? 'active' : ''}
                        onClick={() => setCurrentMoveIdx(idx + 1)}
                      >
                        <td style={{ color: 'var(--text-muted)' }}>
                          {m.color === 'white' ? `${m.full_move}.` : `${m.full_move}...`}
                        </td>
                        <td style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{m.san}</td>
                        <td><ClassPill cls={m.classification} /></td>
                        <td><EvalChip value={m.eval_after} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Blunders Panel */}
          {result.blunders?.length > 0 && (
            <div className="card">
              <div className="section-title">
                <span className="icon">🔴</span> Blunders ({result.blunders.length})
              </div>
              <div className="blunders-grid">
                {result.blunders.map((b, i) => (
                  <div
                    key={i}
                    className="blunder-card"
                    onClick={() => setCurrentMoveIdx(b.move_number)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="blunder-card-header">
                      <span className="blunder-move-num">
                        Move {b.full_move}{b.color === 'black' ? '...' : '.'} ({b.color})
                      </span>
                      <span className="classification-pill pill-blunder">?? blunder</span>
                    </div>
                    <div className="blunder-san">{b.san}</div>
                    <div className="blunder-eval-row">
                      <EvalChip value={b.eval_before} />
                      <span className="arrow">→</span>
                      <EvalChip value={b.eval_after} />
                      <span style={{ color: 'var(--red)', marginLeft: '0.25rem' }}>
                        ({b.eval_delta > 0 ? '+' : ''}{b.eval_delta})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Narrative */}
          {narrative?.game_story && (
            <div className="card">
              <div className="section-title">
                <span className="icon">📖</span> Claude AI Game Narrative
              </div>

              <p className="narrative-story">{narrative.game_story}</p>

              {/* Key Moments */}
              {narrative.key_moments?.length > 0 && (
                <div className="key-moments-list">
                  <div className="section-title" style={{ marginTop: '1.25rem', fontSize: '0.95rem' }}>
                    <span className="icon">⚡</span> Key Moments
                  </div>
                  {narrative.key_moments.map((km, i) => (
                    <div
                      key={i}
                      className="key-moment-item"
                      onClick={() => km.move_number && setCurrentMoveIdx(km.move_number)}
                      style={{ cursor: km.move_number ? 'pointer' : 'default' }}
                    >
                      <div className="key-moment-num">Move {km.move_number}</div>
                      <div className="key-moment-desc">
                        {km.description}
                        {km.significance && (
                          <span className={`significance-badge sig-${km.significance}`}>
                            {km.significance}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Winner / Loser Analysis */}
              {(narrative.winner_analysis || narrative.loser_analysis) && (
                <div className="analysis-row">
                  {narrative.winner_analysis && (
                    <div className="analysis-box winner">
                      <div className="analysis-box-title">✓ Why They Won</div>
                      <p>{narrative.winner_analysis}</p>
                    </div>
                  )}
                  {narrative.loser_analysis && (
                    <div className="analysis-box loser">
                      <div className="analysis-box-title">✗ What Went Wrong</div>
                      <p>{narrative.loser_analysis}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Improvement Tips */}
              {narrative.improvement_tips?.length > 0 && (
                <>
                  <div className="section-title" style={{ marginTop: '1.5rem', fontSize: '0.95rem' }}>
                    <span className="icon">💡</span> Improvement Tips
                  </div>
                  <div className="tips-list">
                    {narrative.improvement_tips.map((tip, i) => (
                      <div key={i} className="tip-item">
                        <div className="tip-num">{i + 1}</div>
                        <div className="tip-text">{tip}</div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {/* Opening Assessment */}
              {narrative.opening_assessment && (
                <div className="opening-box">
                  <strong>Opening Assessment:</strong> {narrative.opening_assessment}
                </div>
              )}
            </div>
          )}

          {/* Reset */}
          <div className="reset-btn-row">
            <button className="btn btn-secondary" onClick={handleReset}>
              ← Analyse Another Game
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
