"""Watch the robot: LED0 to LED3 light up one by one, then all together."""

import time

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_leds():
    with RaspiMouse() as mouse:
        for led in mouse.leds:
            led.on()
            assert led.is_on
            time.sleep(0.5)
            led.off()
            assert not led.is_on
        for led in mouse.leds:
            led.on()
        time.sleep(1.0)
