import React from 'react'

const SEV_LABEL = {
  good: 'Healthy',
  fair: 'Acceptable',
  warning: 'Degrading',
  critical: 'Critical',
  'warming-up': 'Warming up',
}

export default function Prediction({ prediction }) {
  const p = prediction || {}
  const sev = p.severity || 'warming-up'
  return (
    <div className="panel">
      <h2>ML Prediction (next window)</h2>
      <div className="prediction">
        <div className="pred-main">
          <div className="pred-future">{p.future_mos != null ? p.future_mos : '—'}</div>
          <div className={`badge ${sev}`}>{SEV_LABEL[sev]}</div>
          {p.degradation && <div className="badge critical">Degradation likely</div>}
        </div>
        <div className="pred-delta">
          {p.delta != null ? (
            <>
              Δ vs current:&nbsp;
              <strong style={{ color: p.delta < 0 ? 'var(--critical)' : 'var(--good)' }}>
                {p.delta > 0 ? '+' : ''}{p.delta}
              </strong>
            </>
          ) : (
            'Collecting baseline…'
          )}
        </div>
      </div>
    </div>
  )
}
