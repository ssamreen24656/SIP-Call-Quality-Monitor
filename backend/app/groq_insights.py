"""Groq-powered natural-language analysis of call-quality metrics."""

import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client: Groq | None = None


def _get_client() -> Groq | None:
    global _client
    if _client is not None:
        return _client
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key or key == "your_groq_api_key_here":
        return None
    _client = Groq(api_key=key)
    return _client


def get_insights(metrics_summary: dict) -> str:
    client = _get_client()
    if client is None:
        return (
            "Groq API key not configured. Add GROQ_API_KEY to backend/.env "
            "to enable AI insights."
        )

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    prompt = (
        "You are a VoIP/SIP quality monitoring expert. Analyze these recent call "
        "metrics and return concise, actionable insights.\n\n"
        f"Metrics:\n{json.dumps(metrics_summary, indent=2)}\n\n"
        "Provide:\n"
        "1. Current call quality assessment (1-2 sentences).\n"
        "2. Most likely root cause if quality is degrading (1-2 sentences).\n"
        "3. One concrete recommendation.\n\n"
        "Keep total response under 120 words. Be specific and technical."
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=350,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Insights unavailable: {e}"
