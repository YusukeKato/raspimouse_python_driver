"""Light sensors return values in range on the real robot."""

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_light_sensors_read():
    with RaspiMouse() as mouse:
        for _ in range(20):
            values = mouse.light_sensors.read()
            assert all(-4095 <= v <= 4095 for v in values), values
