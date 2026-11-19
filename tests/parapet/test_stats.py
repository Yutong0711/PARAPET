"""Functional tests for parapet.stats (no model, no JDK)."""

from __future__ import annotations

import pytest

from parapet.stats import noise_floor_pct, ratio_of_medians_ci


def test_ratio_of_medians_point_and_ci_are_deterministic():
    a = [110, 111, 109, 112, 108, 110, 111, 109, 110, 110]
    b = [100, 101, 99, 100, 102, 98, 100, 100, 101, 99]
    r1 = ratio_of_medians_ci(a, b, resamples=2000, seed=7)
    r2 = ratio_of_medians_ci(a, b, resamples=2000, seed=7)
    assert r1 == r2
    assert r1["ratio"] == pytest.approx(110 / 100)
    assert r1["ratio_lo"] <= r1["ratio"] <= r1["ratio_hi"]
    assert r1["overhead_pct"] == pytest.approx(10.0)


def test_identical_groups_give_a_ci_around_one():
    a = [100.0 + (i % 5) for i in range(20)]
    r = ratio_of_medians_ci(a, list(a), resamples=2000, seed=1)
    assert r["ratio"] == pytest.approx(1.0)
    assert r["ratio_lo"] <= 1.0 <= r["ratio_hi"]
    assert noise_floor_pct(r) >= 0.0


def test_empty_group_is_an_error():
    with pytest.raises(ValueError):
        ratio_of_medians_ci([], [1.0])
