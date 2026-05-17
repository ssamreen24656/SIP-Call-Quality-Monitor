"""Generate a synthetic RTP PCAP for testing the SIP MOS monitor.

Usage:
    python scripts/generate_sample_pcap.py [output_path] [--duration 30]

The generator produces a single RTP stream (G.711 mu-law, PT=0, 8 kHz, 20 ms
packetization). It injects three quality phases:
  0 - 1/3 duration: clean call
  1/3 - 2/3 duration: rising jitter + packet loss
  2/3 - end:        heavy congestion (high jitter, high loss, high latency)
"""

import argparse
import random

from scapy.all import Ether, IP, UDP, Raw, wrpcap


def build_pcap(out_path: str, duration_s: float = 30.0) -> int:
    ssrc = 0x12345678
    sample_rate = 8000
    pkt_interval = 0.020  # 20 ms
    payload_size = 160  # bytes (G.711 20 ms)
    src_ip, dst_ip = "192.168.1.10", "192.168.1.20"
    src_port, dst_port = 16384, 16386

    packets = []
    base_time = 1_700_000_000.0  # arbitrary epoch
    seq = random.randint(0, 65535)
    ts = random.randint(0, 2**31)

    n = int(duration_s / pkt_interval)
    phase_a = n // 3
    phase_b = 2 * n // 3

    for i in range(n):
        if i < phase_a:
            jitter_s = random.gauss(0, 0.002)   # 2 ms std
            loss_prob = 0.0
            extra_latency = 0.0
        elif i < phase_b:
            jitter_s = random.gauss(0, 0.012)   # 12 ms std
            loss_prob = 0.03
            extra_latency = 0.020
        else:
            jitter_s = random.gauss(0, 0.030)   # 30 ms std
            loss_prob = 0.10
            extra_latency = 0.080

        seq = (seq + 1) % 65536
        ts = (ts + 160) % (2**32)

        if random.random() < loss_prob:
            continue  # simulate packet loss

        arrival = base_time + i * pkt_interval + jitter_s + extra_latency

        rtp_header = bytes([
            0x80,         # V=2, P=0, X=0, CC=0
            0x00,         # M=0, PT=0 (PCMU)
        ]) + seq.to_bytes(2, "big") + ts.to_bytes(4, "big") + ssrc.to_bytes(4, "big")
        rtp_payload = bytes([random.randint(0, 255) for _ in range(payload_size)])

        pkt = (
            Ether()
            / IP(src=src_ip, dst=dst_ip)
            / UDP(sport=src_port, dport=dst_port)
            / Raw(load=rtp_header + rtp_payload)
        )
        pkt.time = arrival
        packets.append(pkt)

    packets.sort(key=lambda p: p.time)
    wrpcap(out_path, packets)
    return len(packets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", default="sample_rtp.pcap")
    parser.add_argument("--duration", type=float, default=30.0)
    args = parser.parse_args()

    count = build_pcap(args.output, args.duration)
    print(f"Wrote {count} RTP packets to {args.output} ({args.duration}s)")


if __name__ == "__main__":
    main()
