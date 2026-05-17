import React, { useEffect, useRef, useState } from 'react'
import Upload from './components/Upload'
import MetricsCards from './components/MetricsCards'
import MetricsChart from './components/MetricsChart'
import Prediction from './components/Prediction'
import AIInsights from './components/AIInsights'
import { openReplaySocket } from './api'

const HISTORY_MAX = 120

export default function App() {
  const [session, setSession] = useState(null)
  const [current, setCurrent] = useState(null)
  const [history, setHistory] = useState([])
  const [streamState, setStreamState] = useState('idle') // idle | live | done | error
  const wsRef = useRef(null)

  useEffect(() => {
    if (!session) return
    setHistory([])
    setCurrent(null)
    setStreamState('live')

    const ws = openReplaySocket(session.session_id, {
      onMessage: (msg) => {
        if (msg.event === 'done') {
          setStreamState('done')
          return
        }
        if (msg.error) {
          setStreamState('error')
          return
        }
        setCurrent(msg)
        setHistory((h) => {
          const next = [...h, msg]
          return next.length > HISTORY_MAX ? next.slice(-HISTORY_MAX) : next
        })
      },
      onClose: () => setStreamState((s) => (s === 'live' ? 'done' : s)),
      onError: () => setStreamState('error'),
    })
    wsRef.current = ws

    return () => {
      try { ws.close() } catch (e) { /* ignore */ }
    }
  }, [session])

  const pillClass = streamState === 'live' ? 'live' : streamState === 'done' ? 'done' : ''
  const pillLabel = {
    idle: 'No session',
    live: 'Live replay',
    done: 'Replay complete',
    error: 'Connection error',
  }[streamState]

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>SIP Call Quality Monitor</h1>
          <div className="subtitle">RTP analysis · MOS scoring · ML degradation prediction · Groq insights</div>
        </div>
        <div className={`status-pill ${pillClass}`}>{pillLabel}</div>
      </header>

      <Upload onSessionReady={setSession} disabled={streamState === 'live'} />

      {session && (
        <div className="panel" style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div><div className="muted" style={{ fontSize: 11, textTransform: 'uppercase' }}>File</div><div>{session.filename}</div></div>
          <div><div className="muted" style={{ fontSize: 11, textTransform: 'uppercase' }}>Windows</div><div>{session.total_windows}</div></div>
          <div><div className="muted" style={{ fontSize: 11, textTransform: 'uppercase' }}>Duration</div><div>{session.duration_seconds}s</div></div>
          <div><div className="muted" style={{ fontSize: 11, textTransform: 'uppercase' }}>RTP streams</div><div>{session.streams.length}</div></div>
        </div>
      )}

      <MetricsCards current={current} />
      <Prediction prediction={current?.prediction} />
      <MetricsChart history={history} />
      <AIInsights sessionId={session?.session_id} disabled={streamState === 'live'} />

      <div className="muted" style={{ fontSize: 12, marginTop: 24, textAlign: 'center' }}>
        Replay runs at ~4x real-time. AI Insights are best generated once replay is complete.
      </div>
    </div>
  )
}
