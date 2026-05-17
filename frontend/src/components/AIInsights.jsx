import React, { useState } from 'react'
import { fetchInsights } from '../api'

export default function AIInsights({ sessionId, disabled }) {
  const [insight, setInsight] = useState(null)
  const [summary, setSummary] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    if (!sessionId) return
    setBusy(true); setError(null)
    try {
      const data = await fetchInsights(sessionId)
      setInsight(data.insight)
      setSummary(data.summary)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Failed to fetch insights')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <div className="row" style={{ marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>AI Insights (Groq)</h2>
        <div className="spacer" />
        <button className="btn secondary" onClick={run} disabled={!sessionId || busy || disabled}>
          {busy ? 'Analyzing…' : insight ? 'Refresh' : 'Generate'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      <div className="insights-body">
        {busy && <div className="insights-loading">Calling Groq…</div>}
        {!busy && !insight && (
          <div className="insights-loading">
            Upload a pcap and click <strong>Generate</strong> for an AI diagnosis of recent call quality.
          </div>
        )}
        {!busy && insight && insight}
      </div>
      {summary && (
        <div className="muted" style={{ marginTop: 10, fontSize: 12 }}>
          Based on {summary.windows_analyzed} windows · avg MOS {summary.avg_mos} ·
          jitter {summary.avg_jitter_ms}ms · loss {summary.avg_packet_loss_pct}% ·
          latency {summary.avg_latency_ms}ms
        </div>
      )}
    </div>
  )
}
