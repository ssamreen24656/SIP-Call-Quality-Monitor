"""Parse a PCAP file and extract per-window RTP quality metrics."""

import struct
from collections import defaultdict

from scapy.all import rdpcap, UDP


def _parse_rtp_header(payload: bytes):
    if len(payload) < 12:
        return None

    byte0 = payload[0]
    version = (byte0 >> 6) & 0x03
    if version != 2:
        return None

    payload_type = payload[1] & 0x7F
    # Audio PTs: 0-34 (static) or 96-127 (dynamic). Filter obvious non-RTP.
    if 35 <= payload_type < 96:
        return None

    sequence = struct.unpack("!H", payload[2:4])[0]
    timestamp = struct.unpack("!I", payload[4:8])[0]
    ssrc = struct.unpack("!I", payload[8:12])[0]
    return {
        "payload_type": payload_type,
        "sequence": sequence,
        "timestamp": timestamp,
        "ssrc": ssrc,
    }


def extract_rtp_metrics(pcap_path: str, window_seconds: float = 1.0):
    """Return a time-sorted list of per-window metrics per RTP stream.

    Each entry: {time, ssrc, jitter_ms, packet_loss_pct, latency_ms}.
    """
    packets = rdpcap(pcap_path)
    streams = defaultdict(list)

    for pkt in packets:
        if not pkt.haslayer(UDP):
            continue
        udp = pkt[UDP]
        if udp.sport < 1024 or udp.dport < 1024:
            continue
        payload = bytes(udp.payload)
        rtp = _parse_rtp_header(payload)
        if rtp is None:
            continue
        streams[rtp["ssrc"]].append(
            {
                "arrival": float(pkt.time),
                "sequence": rtp["sequence"],
                "timestamp": rtp["timestamp"],
            }
        )

    if not streams:
        return []

    all_metrics = []
    clock_rate = 8000  # G.711-style default; adequate for jitter math

    for ssrc, pkts in streams.items():
        if len(pkts) < 10:
            continue
        pkts.sort(key=lambda p: p["arrival"])

        # RFC 3550 jitter computed packet-by-packet
        jitter_series = []
        prev_arrival = pkts[0]["arrival"]
        prev_ts = pkts[0]["timestamp"]
        jitter = 0.0
        for p in pkts[1:]:
            d_arr = (p["arrival"] - prev_arrival) * clock_rate
            d_ts = p["timestamp"] - prev_ts
            D = abs(d_arr - d_ts)
            jitter += (D - jitter) / 16.0
            jitter_series.append((p["arrival"], jitter * 1000.0 / clock_rate))
            prev_arrival = p["arrival"]
            prev_ts = p["timestamp"]

        start = pkts[0]["arrival"]
        end = pkts[-1]["arrival"]
        t = start
        while t < end:
            w_end = t + window_seconds
            w_pkts = [p for p in pkts if t <= p["arrival"] < w_end]
            w_jitters = [j for ta, j in jitter_series if t <= ta < w_end]
            if not w_pkts:
                t = w_end
                continue

            seqs = sorted(p["sequence"] for p in w_pkts)
            if len(seqs) > 1:
                expected = (seqs[-1] - seqs[0] + 1) % 65536
                expected = expected if expected > 0 else len(seqs)
                lost = max(0, expected - len(seqs))
                loss_pct = (lost / expected) * 100.0 if expected > 0 else 0.0
            else:
                loss_pct = 0.0

            avg_jitter = sum(w_jitters) / len(w_jitters) if w_jitters else 0.0

            arrivals = sorted(p["arrival"] for p in w_pkts)
            if len(arrivals) > 1:
                deltas = [(arrivals[i + 1] - arrivals[i]) * 1000.0 for i in range(len(arrivals) - 1)]
                latency = sum(deltas) / len(deltas)
            else:
                latency = 20.0

            all_metrics.append(
                {
                    "time": round(t - start, 2),
                    "ssrc": f"{ssrc:08x}",
                    "jitter_ms": round(avg_jitter, 2),
                    "packet_loss_pct": round(loss_pct, 2),
                    "latency_ms": round(latency, 2),
                }
            )
            t = w_end

    all_metrics.sort(key=lambda m: (m["time"], m["ssrc"]))
    return all_metrics
