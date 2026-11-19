# SPDX-License-Identifier: Apache-2.0
"""Ratio of medians with a percentile bootstrap interval."""

from __future__ import annotations

import numpy as np


def median(xs) -> float:
    return float(np.median(np.asarray(xs, dtype=float)))


def ratio_of_medians_ci(arm, base, *, resamples: int = 10000, confidence: float = 0.95,
                        seed: int = 20261119) -> dict:
    """Point estimate median(arm)/median(base) and a percentile bootstrap CI.

    Forks are resampled with replacement independently within each group.
    Deterministic for a given seed.
    """
    a = np.asarray(arm, dtype=float)
    b = np.asarray(base, dtype=float)
    if a.size == 0 or b.size == 0:
        raise ValueError("both groups need at least one sample")
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, a.size, size=(resamples, a.size))
    ib = rng.integers(0, b.size, size=(resamples, b.size))
    ratios = np.median(a[ia], axis=1) / np.median(b[ib], axis=1)
    alpha = (1.0 - confidence) / 2.0
    lo, hi = np.quantile(ratios, [alpha, 1.0 - alpha])
    point = float(np.median(a) / np.median(b))
    return {
        "ratio": point,
        "ratio_lo": float(lo),
        "ratio_hi": float(hi),
        "overhead_pct": (point - 1.0) * 100.0,
        "overhead_pct_lo": (float(lo) - 1.0) * 100.0,
        "overhead_pct_hi": (float(hi) - 1.0) * 100.0,
        "n_arm": int(a.size),
        "n_base": int(b.size),
        "resamples": resamples,
        "confidence": confidence,
        "seed": seed,
    }


def noise_floor_pct(aa: dict) -> float:
    return max(abs(aa["ratio_lo"] - 1.0), abs(aa["ratio_hi"] - 1.0)) * 100.0
