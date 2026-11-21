"""Pulse counters answer on I2C and do not count while the motors are stopped."""

import time

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_pulse_counters_idle():
    with RaspiMouse() as mouse:
        counters = (mouse.left_counter, mouse.right_counter)
        raw = [c.read_raw() for c in counters]
        assert all(0 <= r <= 0xFFFF for r in raw)
        time.sleep(0.5)
        assert [c.read_raw() for c in counters] == raw
        assert [c.read_signed() for c in counters] == [0, 0]
