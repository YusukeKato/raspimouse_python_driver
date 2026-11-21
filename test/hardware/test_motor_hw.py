"""
The robot moves! Run only with RASPIMOUSE_MOTOR_TEST=1, on the floor or with wheels lifted.

Forward 1 s, backward 1 s, turn left 1 s, turn right 1 s at 400 Hz
(slower speeds make the stepper motors noisy). After each step the signed
pulse counts must have changed by about 400 in the commanded direction.
"""

import os
import time

import pytest

from raspimouse_python_driver import RaspiMouse

FREQUENCY_HZ = 400
DURATION_S = 1.0
# Allowed difference from FREQUENCY_HZ * DURATION_S pulses (timing jitter).
TOLERANCE = 40


@pytest.mark.hardware
@pytest.mark.skipif(os.environ.get('RASPIMOUSE_MOTOR_TEST') != '1',
                    reason='set RASPIMOUSE_MOTOR_TEST=1 to run the motors')
def test_motors():
    f = FREQUENCY_HZ
    expected = round(f * DURATION_S)
    with RaspiMouse() as mouse:
        counters = (mouse.left_counter, mouse.right_counter)
        mouse.motor_power.on()
        for left, right in ((f, f), (-f, -f), (-f, f), (f, -f)):
            before = [c.read_signed() for c in counters]
            mouse.motors.set_frequency(left, right)
            assert (mouse.motors.left.frequency_hz, mouse.motors.right.frequency_hz) == \
                (left, right)
            time.sleep(DURATION_S)
            mouse.motors.stop()
            moved = [c.read_signed() - b for c, b in zip(counters, before)]
            for pulses, frequency in zip(moved, (left, right)):
                sign = 1 if frequency > 0 else -1
                assert abs(pulses - sign * expected) <= TOLERANCE, (left, right, moved)
        mouse.motor_power.off()
