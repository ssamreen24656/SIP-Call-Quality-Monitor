# AI-Powered SIP Call Quality Monitor

Capture RTP from a PCAP, extract MOS metrics (jitter, packet loss, latency),
feed them into a scikit-learn predictor to forecast call-quality degradation,
and use Groq for natural-language diagnosis.

- **Backend:** FastAPI + scapy + scikit-learn + Groq SDK
- **Frontend:** React (Vite) + recharts
- **Data flow:** upload `.pcap` → parse RTP → MOS score per 1s window → ML predicts next-window MOS → WebSocket streams to UI → Groq summarizes

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # add your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

Backend will train the synthetic model on startup (a few seconds) and listen on `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### 3. Generate a test PCAP

If you don't already have a pcap with RTP traffic, generate one:

```bash
cd backend
source .venv/bin/activate
python scripts/generate_sample_pcap.py sample_rtp.pcap --duration 30
```

This produces a 30s synthetic RTP stream with three quality phases (clean → degrading → congested). Upload it from the UI.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET  | `/health` | health check |
| POST | `/upload-pcap` | multipart upload, returns `session_id` |
| GET  | `/sessions/{id}/insights` | Groq diagnosis of last 20 windows |
| WS   | `/ws/replay/{id}` | streams per-window metrics + ML prediction |

## How MOS is computed

E-Model approximation:
- `R = 93.2 − Id − Ie`, where `Id` is delay impairment from `latency + 2*jitter + 10` and `Ie` is loss impairment `30 * loss/(loss+10)`
- `MOS = 1 + 0.035·R + 7e-6·R·(R-60)·(100-R)`, clamped to `[1.0, 4.5]`

## How the ML model works

- `GradientBoostingRegressor`, 120 estimators
- Trained on startup on 3000 synthetic 6-window sequences (5 lookback + 1 target)
- 30% of training sequences include an injected degradation trend so the model learns to project worsening conditions forward
- Input: flattened `[jitter, loss, latency]` over the previous 5 windows
- Output: predicted MOS for the next window

Per window the server emits both the measured MOS and the predicted MOS plus a `degradation` flag and severity (`good` / `fair` / `warning` / `critical`).

## Project layout

```
backend/
  app/
    main.py            # FastAPI + WebSocket
    pcap_parser.py     # scapy RTP extraction, RFC 3550 jitter
    mos.py             # E-Model MOS
    ml_model.py        # GradientBoostingRegressor
    groq_insights.py   # Groq SDK wrapper
  scripts/
    generate_sample_pcap.py
  requirements.txt
  .env.example
frontend/
  src/
    App.jsx
    api.js
    components/
      Upload.jsx
      MetricsCards.jsx
      MetricsChart.jsx
      Prediction.jsx
      AIInsights.jsx
    styles.css
  package.json
  vite.config.js
  index.html
```

## Notes & limits

- One-way RTP latency cannot be measured directly from a single capture; the parser approximates it from inter-arrival deltas. For accurate one-way latency you'd correlate RTCP SR/RR or a synced capture at both endpoints.
- The pcap heuristic requires `version=2` RTP headers on a high UDP port pair. SIP signaling and RTCP packets are ignored.
- The synthetic-trained model is meant to demonstrate the inference path. For production, retrain on real labeled call data.
- Replay speed is hard-coded to ~4x real-time (250 ms per 1 s window). Adjust the `await asyncio.sleep(0.25)` in `app/main.py`.
