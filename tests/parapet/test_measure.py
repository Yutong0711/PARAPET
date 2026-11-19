"""The peak-memory sample must belong to the measured process only (no model)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from parapet.measure import GNU_TIME, schedule

HAS_TIME = Path(GNU_TIME).is_file()


@pytest.mark.skipif(not HAS_TIME or not sys.platform.startswith("linux"), reason="needs Linux and GNU time")
def test_gnu_time_reports_the_child_not_the_parent(tmp_path):
    ballast = bytearray(120 * 1024 * 1024)
    ballast[::4096] = b"x" * len(ballast[::4096])  # raise this process's RSS high-water mark
    out = tmp_path / "rss.txt"
    p = subprocess.Popen([GNU_TIME, "-f", "%M", "-o", str(out), "true"], start_new_session=True)
    _, status, rusage = os.wait4(p.pid, 0)
    p.returncode = os.waitstatus_to_exitcode(status)
    child_kib = int(out.read_text().split()[-1])
    # wait4 on our own child inherits our high-water mark; GNU time's %M does not.
    assert rusage.ru_maxrss > 100 * 1024
    assert child_kib < 20 * 1024
    del ballast


def test_schedule_interleaves_every_arm_once_per_fork_index():
    plan = schedule(["a", "b", "c"], forks=4, seed=1)
    assert len(plan) == 12
    for i in range(4):
        assert sorted(a for (k, _, a) in plan if k == i) == ["a", "b", "c"]
    assert plan == schedule(["a", "b", "c"], forks=4, seed=1)
