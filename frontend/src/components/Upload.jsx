import React, { useRef, useState } from 'react'
import { uploadPcap } from '../api'

export default function Upload({ onSessionReady, disabled }) {
  const inputRef = useRef(null)
  const [file, setFile] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const submit = async () => {
    if (!file) return
    setBusy(true); setError(null)
    try {
      const data = await uploadPcap(file)
      onSessionReady(data)
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <h2>Upload PCAP</h2>
      {error && <div className="error">{error}</div>}
      <div className="upload-row">
        <input
          ref={inputRef}
          type="file"
          accept=".pcap,.pcapng,.cap"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          disabled={disabled || busy}
        />
        <button className="btn" onClick={submit} disabled={!file || busy || disabled}>
          {busy ? 'Parsing…' : 'Analyze'}
        </button>
        <div className="upload-meta">
          {file ? `${file.name} · ${(file.size / 1024).toFixed(1)} KB` : 'Select a .pcap with RTP traffic'}
        </div>
      </div>
    </div>
  )
}
