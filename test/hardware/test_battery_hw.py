"""
The battery voltage reads in a plausible range.

It is the input voltage after the main switch, so with an AC adapter it is
the adapter voltage. The robot is running, so it cannot be near 0 V.
"""

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_battery_voltage():
    with RaspiMouse() as mouse:
        voltage = mouse.battery.read_voltage()
        assert 5.0 <= voltage <= 13.5, voltage
