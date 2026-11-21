"""Listen: the buzzer plays a low, a middle and a high tone, then stops."""

import time

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
def test_buzzer():
    with RaspiMouse() as mouse:
        for frequency in (440, 880, 1760):
            mouse.buzzer.play(frequency)
            assert mouse.buzzer.frequency_hz == frequency
            time.sleep(0.5)
        mouse.buzzer.stop()
        assert mouse.buzzer.frequency_hz == 0
