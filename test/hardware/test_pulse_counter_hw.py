"""Pulse counters answer on I2C, stay still when idle and never jump under fast pulses."""

import time

import pytest

from raspimouse_python_driver import RaspiMouse

FAST_HZ = 5000
FAST_DURATION_S = 5.0


@pytest.mark.hardware
def test_pulse_counters_idle():
    with RaspiMouse() as mouse:
        counters = (mouse.left_counter, mouse.right_counter)
        raw = [c.read_raw() for c in counters]
        assert all(0 <= r <= 0xFFFF for r in raw)
        time.sleep(0.5)
        assert [c.read_raw() for c in counters] == raw
        assert [c.read_signed() for c in counters] == [0, 0]


@pytest.mark.hardware
def test_pulse_counters_under_fast_pulses():
    """
    Send 5 kHz step pulses with the motor power OFF, so the robot does not move.

    The LSB of the counters then wraps every 51 ms. Reading LSB and MSB in two
    I2C transfers could catch a carry between them (issue #2); the counts must
    never jump and must match the pulses sent.
    """
    with RaspiMouse() as mouse:
        assert not mouse.motor_power.is_on
        counters = (mouse.left_counter, mouse.right_counter)
        last = [c.read_signed() for c in counters]
        start = time.monotonic()
        mouse.motors.set_frequency(FAST_HZ, FAST_HZ)
        reads = 0
        try:
            while time.monotonic() - start < FAST_DURATION_S:
                values = [c.read_signed() for c in counters]
                steps = [v - p for v, p in zip(values, last)]
                assert all(0 <= s <= 500 for s in steps), steps
                last = values
                reads += 1
        finally:
            mouse.motors.stop()
            elapsed = time.monotonic() - start
        totals = [c.read_signed() for c in counters]
        print(f'\n{reads} reads, totals {totals}, expected about {FAST_HZ * elapsed:.0f}')
        for total in totals:
            assert total == pytest.approx(FAST_HZ * elapsed, rel=0.02)
