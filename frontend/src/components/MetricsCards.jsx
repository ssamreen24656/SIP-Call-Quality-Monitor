import React from 'react'

function mosClass(mos) {
  if (mos == null) return ''
  if (mos >= 4.0) return 'good'
  if (mos >= 3.6) return 'fair'
  if (mos >= 3.0) return 'warning'
  return 'critical'
}

function jitterClass(j) {
  if (j == null) return ''
  if (j < 15) return 'good'
  if (j < 30) return 'fair'
  if (j < 60) return 'warning'
  return 'critical'
}

function lossClass(l) {
  if (l == null) return ''
  if (l < 1) return 'good'
  if (l < 3) return 'fair'
  if (l < 7) return 'warning'
  return 'critical'
}

function latencyClass(l) {
  if (l == null) return ''
  if (l < 60) return 'good'
  if (l < 150) return 'fair'
  if (l < 300) return 'warning'
  return 'critical'
}

function Card({ label, value, unit, cls }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className={`value ${cls}`}>
        {value != null ? value : '—'}
        {unit && <span className="unit">{unit}</span>}
      </div>
    </div>
  )
}

export default function MetricsCards({ current }) {
  const c = current || {}
  return (
    <div className="panel">
      <h2>Live Metrics</h2>
      <div className="cards">
        <Card label="MOS" value={c.mos} cls={mosClass(c.mos)} />
        <Card label="Jitter" value={c.jitter_ms} unit="ms" cls={jitterClass(c.jitter_ms)} />
        <Card label="Packet Loss" value={c.packet_loss_pct} unit="%" cls={lossClass(c.packet_loss_pct)} />
        <Card label="Latency" value={c.latency_ms} unit="ms" cls={latencyClass(c.latency_ms)} />
      </div>
    </div>
  )
}
