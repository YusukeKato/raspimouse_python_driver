"""
The robot moves! Run only with RASPIMOUSE_MOTOR_TEST=1, on the floor.

Drives 0.3 m forward at 0.15 m/s, then turns 90 degrees to the left at pi rad/s,
by velocity commands sent at 20 Hz like a ROS node. Both run the wheels at about
400 Hz (slower is noisy). Checks the odometry from the pulse counters.
Measure the real distance and angle by hand to check the wheel parameters.
"""

import math
import os
import time

import pytest

from raspimouse_python_driver import RaspiMouse


def drive_for(mouse, linear, angular, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        mouse.drive.set_velocity(linear, angular)
        time.sleep(0.05)
    mouse.drive.stop()
    deadline = time.monotonic() + 3.0
    while mouse.drive.wheel_frequencies != (0, 0) and time.monotonic() < deadline:
        time.sleep(0.02)
    time.sleep(0.1)


@pytest.mark.hardware
@pytest.mark.skipif(os.environ.get('RASPIMOUSE_MOTOR_TEST') != '1',
                    reason='set RASPIMOUSE_MOTOR_TEST=1 to run the motors')
def test_drive_forward_then_turn_left():
    with RaspiMouse() as mouse:
        mouse.motor_power.on()
        drive_for(mouse, 0.15, 0.0, 2.0)
        odom = mouse.drive.odometry()
        print(f'\nforward: x {odom.x:.3f} m, y {odom.y:.3f} m, '
              f'theta {math.degrees(odom.theta):.1f} deg')
        assert odom.x == pytest.approx(0.3, abs=0.03)
        assert abs(odom.y) < 0.01 and abs(odom.theta) < math.radians(5)

        mouse.drive.reset_odometry()
        drive_for(mouse, 0.0, math.pi, 0.5)
        odom = mouse.drive.odometry()
        print(f'turn: theta {math.degrees(odom.theta):.1f} deg')
        assert odom.theta == pytest.approx(math.pi / 2, abs=math.radians(15))
        mouse.motor_power.off()
