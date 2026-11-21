"""
The robot moves! Run only with RASPIMOUSE_MOTOR_TEST=1, on the floor or with wheels lifted.

Forward 1 s, backward 1 s, turn left 1 s, turn right 1 s at 400 Hz
(slower speeds make the stepper motors noisy).
"""

import os
import time

import pytest

from raspimouse_python_driver import RaspiMouse


@pytest.mark.hardware
@pytest.mark.skipif(os.environ.get('RASPIMOUSE_MOTOR_TEST') != '1',
                    reason='set RASPIMOUSE_MOTOR_TEST=1 to run the motors')
def test_motors():
    with RaspiMouse() as mouse:
        mouse.motor_power.on()
        for left, right in ((400, 400), (-400, -400), (-400, 400), (400, -400)):
            mouse.motors.set_frequency(left, right)
            assert (mouse.motors.left.frequency_hz, mouse.motors.right.frequency_hz) == \
                (left, right)
            time.sleep(1.0)
        mouse.motors.stop()
        mouse.motor_power.off()
