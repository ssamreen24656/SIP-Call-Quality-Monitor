"""Call-quality predictor: GradientBoostingRegressor trained on synthetic sequences."""

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from .mos import calculate_mos


class CallQualityPredictor:
    LOOKBACK = 5

    def __init__(self) -> None:
        self.model: GradientBoostingRegressor | None = None
        self._train_synthetic()

    def _train_synthetic(self, n_sequences: int = 3000) -> None:
        rng = np.random.default_rng(42)
        X, y = [], []

        for _ in range(n_sequences):
            base_jitter = rng.uniform(1, 30)
            base_loss = rng.uniform(0, 5)
            base_latency = rng.uniform(20, 200)
            degrade = rng.random() < 0.35

            seq = []
            for t in range(self.LOOKBACK + 1):
                trend = (t / self.LOOKBACK) * 50.0 if degrade else 0.0
                jitter = max(0, base_jitter + rng.normal(0, 2) + trend * 0.3)
                loss = max(0, min(100, base_loss + rng.normal(0, 0.5) + trend * 0.1))
                latency = max(0, base_latency + rng.normal(0, 5) + trend)
                seq.append([jitter, loss, latency])

            feat = np.array(seq[: self.LOOKBACK]).flatten()
            future = seq[self.LOOKBACK]
            X.append(feat)
            y.append(calculate_mos(future[0], future[1], future[2]))

        self.model = GradientBoostingRegressor(
            n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42
        )
        self.model.fit(np.array(X), np.array(y))

    def predict_future_mos(self, recent_windows: list[list[float]]) -> float | None:
        if len(recent_windows) < self.LOOKBACK or self.model is None:
            return None
        feat = np.array(recent_windows[-self.LOOKBACK :]).flatten().reshape(1, -1)
        return float(round(self.model.predict(feat)[0], 2))

    def predict_degradation(self, recent_windows: list[list[float]], current_mos: float) -> dict:
        future_mos = self.predict_future_mos(recent_windows)
        if future_mos is None:
            return {
                "future_mos": None,
                "delta": None,
                "degradation": False,
                "severity": "warming-up",
            }

        delta = round(future_mos - current_mos, 2)
        degrading = (current_mos - future_mos) > 0.3

        if future_mos < 2.5:
            severity = "critical"
        elif future_mos < 3.2:
            severity = "warning"
        elif future_mos < 3.8:
            severity = "fair"
        else:
            severity = "good"

        return {
            "future_mos": future_mos,
            "delta": delta,
            "degradation": degrading,
            "severity": severity,
        }
