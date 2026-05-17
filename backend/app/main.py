"""FastAPI app: PCAP upload, replay over WebSocket, Groq insights."""

import asyncio
import os
import tempfile
import uuid
from collections import deque

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .groq_insights import get_insights
from .ml_model import CallQualityPredictor
from .mos import calculate_mos
from .pcap_parser import extract_rtp_metrics

app = FastAPI(title="SIP Call Quality Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = CallQualityPredictor()
SESSIONS: dict[str, dict] = {}


@app.get("/health")
def health():
    return {"status": "ok", "model": "ready" if predictor.model else "not-loaded"}


@app.post("/upload-pcap")
async def upload_pcap(file: UploadFile = File(...)):
    name = file.filename or ""
    if not name.lower().endswith((".pcap", ".pcapng", ".cap")):
        raise HTTPException(400, "File must be .pcap, .pcapng, or .cap")

    suffix = os.path.splitext(name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        metrics = extract_rtp_metrics(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    if not metrics:
        raise HTTPException(400, "No RTP streams detected in pcap")

    for m in metrics:
        m["mos"] = calculate_mos(m["jitter_ms"], m["packet_loss_pct"], m["latency_ms"])

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"metrics": metrics, "filename": name}

    return {
        "session_id": session_id,
        "filename": name,
        "total_windows": len(metrics),
        "duration_seconds": round(metrics[-1]["time"] - metrics[0]["time"], 2) if len(metrics) > 1 else 0,
        "streams": sorted({m["ssrc"] for m in metrics}),
    }


@app.get("/sessions/{session_id}/insights")
def session_insights(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(404, "Session not found")
    metrics = SESSIONS[session_id]["metrics"]
    recent = metrics[-20:] if len(metrics) >= 20 else metrics
    summary = {
        "avg_mos": round(sum(m["mos"] for m in recent) / len(recent), 2),
        "avg_jitter_ms": round(sum(m["jitter_ms"] for m in recent) / len(recent), 2),
        "avg_packet_loss_pct": round(sum(m["packet_loss_pct"] for m in recent) / len(recent), 2),
        "avg_latency_ms": round(sum(m["latency_ms"] for m in recent) / len(recent), 2),
        "min_mos": round(min(m["mos"] for m in recent), 2),
        "max_jitter_ms": round(max(m["jitter_ms"] for m in recent), 2),
        "max_packet_loss_pct": round(max(m["packet_loss_pct"] for m in recent), 2),
        "windows_analyzed": len(recent),
    }
    return {"summary": summary, "insight": get_insights(summary)}


@app.websocket("/ws/replay/{session_id}")
async def ws_replay(websocket: WebSocket, session_id: str):
    await websocket.accept()
    if session_id not in SESSIONS:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    metrics = SESSIONS[session_id]["metrics"]
    history = deque(maxlen=predictor.LOOKBACK)

    try:
        for m in metrics:
            history.append([m["jitter_ms"], m["packet_loss_pct"], m["latency_ms"]])
            prediction = predictor.predict_degradation(list(history), m["mos"])
            await websocket.send_json({**m, "prediction": prediction})
            await asyncio.sleep(0.25)  # ~4x real-time replay
        await websocket.send_json({"event": "done"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
