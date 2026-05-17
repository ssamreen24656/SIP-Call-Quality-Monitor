"""MOS calculation via ITU-T E-Model approximation."""


def calculate_mos(jitter_ms: float, packet_loss_pct: float, latency_ms: float) -> float:
    effective_latency = latency_ms + 2.0 * jitter_ms + 10.0

    if effective_latency < 160.0:
        Id = effective_latency / 40.0
    else:
        Id = (effective_latency - 120.0) / 10.0

    if packet_loss_pct > 0:
        Ie = 30.0 * (packet_loss_pct / (packet_loss_pct + 10.0))
    else:
        Ie = 0.0

    R = 93.2 - Id - Ie
    R = max(0.0, min(100.0, R))

    if R < 1:
        mos = 1.0
    else:
        mos = 1.0 + 0.035 * R + 7e-6 * R * (R - 60.0) * (100.0 - R)

    return round(max(1.0, min(4.5, mos)), 2)
