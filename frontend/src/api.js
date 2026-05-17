import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function uploadPcap(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await axios.post(`${API_BASE}/upload-pcap`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function fetchInsights(sessionId) {
  const { data } = await axios.get(`${API_BASE}/sessions/${sessionId}/insights`)
  return data
}

export function openReplaySocket(sessionId, { onMessage, onClose, onError }) {
  const wsBase = API_BASE.replace(/^http/, 'ws')
  const ws = new WebSocket(`${wsBase}/ws/replay/${sessionId}`)
  ws.onmessage = (ev) => {
    try { onMessage(JSON.parse(ev.data)) } catch (e) { /* ignore */ }
  }
  ws.onclose = () => onClose && onClose()
  ws.onerror = (e) => onError && onError(e)
  return ws
}
