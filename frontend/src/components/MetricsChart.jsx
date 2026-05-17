import React from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

export default function MetricsChart({ history }) {
  const data = history.map((m) => ({
    time: m.time,
    MOS: m.mos,
    'Predicted MOS': m.prediction?.future_mos ?? null,
    Jitter: m.jitter_ms,
    Loss: m.packet_loss_pct,
    Latency: m.latency_ms,
  }))

  return (
    <div className="panel">
      <h2>Trends</h2>
      <div style={{ width: '100%', height: 280 }}>
        <ResponsiveContainer>
          <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#243046" strokeDasharray="3 3" />
            <XAxis dataKey="time" stroke="#8aa0bd" tickFormatter={(t) => `${t.toFixed(0)}s`} />
            <YAxis yAxisId="left" stroke="#8aa0bd" domain={[1, 4.5]} />
            <YAxis yAxisId="right" orientation="right" stroke="#8aa0bd" />
            <Tooltip contentStyle={{ background: '#131a26', border: '1px solid #243046' }} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="MOS" stroke="#5ec2ff" dot={false} strokeWidth={2} />
            <Line yAxisId="left" type="monotone" dataKey="Predicted MOS" stroke="#facc15" dot={false} strokeDasharray="4 4" />
            <Line yAxisId="right" type="monotone" dataKey="Jitter" stroke="#fb923c" dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="Loss" stroke="#f87171" dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="Latency" stroke="#4ade80" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
