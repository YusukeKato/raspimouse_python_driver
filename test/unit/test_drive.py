import math
import time
from unittest import mock

import pytest

from raspimouse_python_driver.config import DriveConfig, MotorConfig
from raspimouse_python_driver.devices.motor import Motors, StepperMotor
from raspimouse_python_driver.drive import Drive
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockDigitalOutput, MockPwmChannel
from raspimouse_python_driver.kinematics import velocity_to_wheel_frequencies

MOTOR_CONFIG = MotorConfig()
CONFIG = DriveConfig()


class Clock:

    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class Counter:

    def __init__(self):
        self.value = 0

    def read_signed(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def make_drive(config=CONFIG, counters=True):
    pwms = (MockPwmChannel(), MockPwmChannel())
    motors = Motors(*(
        StepperMotor(pwm, MockDigitalOutput(ch.direction_pin), ch, MOTOR_CONFIG)
        for pwm, ch in zip(pwms, (MOTOR_CONFIG.left, MOTOR_CONFIG.right))))
    left, right = (Counter(), Counter()) if counters else (None, None)
    clock = Clock()
    drive = Drive(motors, config, left, right, clock=clock, auto_start=False)
    return drive, motors, pwms, (left, right), clock


def run(drive, clock, seconds, period=0.02):
    for _ in range(round(seconds / period)):
        clock.now += period
        drive.update()


def test_ramps_up_within_the_acceleration_limit():
    drive, motors, pwms, _, clock = make_drive()
    drive.set_velocity(0.1, 0)
    drive.update()                 # first cycle only sets the time base
    clock.now += 0.02
    drive.update()
    step = CONFIG.max_wheel_acceleration_hz_s * 0.02
    assert drive.wheel_frequencies == pytest.approx((step, step))
    run(drive, clock, 0.4)   # within the command timeout
    goal = velocity_to_wheel_frequencies(0.1, 0, CONFIG)
    assert drive.wheel_frequencies == pytest.approx(goal)
    assert pwms[0].frequency_hz == pytest.approx(goal[0])
    assert motors.left.frequency_hz > 0 and motors.right.frequency_hz > 0


def test_turning_left_makes_the_right_wheel_faster():
    drive, motors, _, _, clock = make_drive()
    drive.set_velocity(0.1, 1.0)
    drive.update()
    run(drive, clock, 0.4)
    left, right = drive.wheel_frequencies
    assert right > left > 0


def test_speed_limit_keeps_the_path():
    drive, _, _, _, clock = make_drive(DriveConfig(command_timeout_s=0))
    drive.set_velocity(2.0, 2.0)   # far beyond the limit
    drive.update()
    run(drive, clock, 1.0)
    left, right = drive.wheel_frequencies
    goal = velocity_to_wheel_frequencies(2.0, 2.0, CONFIG)
    assert max(abs(left), abs(right)) == pytest.approx(CONFIG.max_wheel_frequency_hz)
    assert left / right == pytest.approx(goal[0] / goal[1])


def test_reversing_ramps_through_zero():
    drive, motors, _, _, clock = make_drive()
    drive.set_velocity(0.1, 0)
    drive.update()
    run(drive, clock, 0.4)
    drive.set_velocity(-0.1, 0)
    seen = []
    for _ in range(40):
        clock.now += 0.02
        drive.update()
        seen.append(drive.wheel_frequencies[0])
    assert min(abs(f) for f in seen) < 50   # passed (close to) zero
    assert not motors.left.is_forward


def test_watchdog_stops_without_commands():
    drive, _, _, _, clock = make_drive()
    drive.set_velocity(0.1, 0)
    drive.update()
    # Patch the logger: ROS pytest plugins may reconfigure logging, so caplog is unreliable.
    with mock.patch('raspimouse_python_driver.drive._logger') as logger:
        run(drive, clock, CONFIG.command_timeout_s - 0.1)
        assert drive.target_velocity == (0.1, 0)
        run(drive, clock, 0.2)
    assert drive.target_velocity == (0, 0)
    logger.warning.assert_called_once()
    assert 'no velocity command' in logger.warning.call_args.args[0]
    run(drive, clock, 1.0)
    assert drive.wheel_frequencies == (0, 0)


def test_repeated_commands_keep_it_moving():
    drive, _, _, _, clock = make_drive()
    drive.update()
    for _ in range(30):            # 1.5 s of commands at 20 Hz
        drive.set_velocity(0.1, 0)
        run(drive, clock, 0.05, period=0.05)
    assert drive.target_velocity == (0.1, 0)


def test_watchdog_can_be_disabled():
    drive, _, _, _, clock = make_drive(DriveConfig(command_timeout_s=0))
    drive.set_velocity(0.1, 0)
    drive.update()
    run(drive, clock, 5.0)
    assert drive.target_velocity == (0.1, 0)


def test_motors_are_written_only_on_change():
    drive, _, pwms, _, clock = make_drive()
    drive.update()
    run(drive, clock, 1.0)             # idle: never touches the motors
    assert pwms[0].history == []
    drive.set_velocity(0.1, 0)
    run(drive, clock, 0.3)
    writes = len(pwms[0].history)
    drive.set_velocity(0.1, 0)
    run(drive, clock, 0.2)             # at target: no more writes
    assert len(pwms[0].history) == writes


def test_odometry_from_counters():
    drive, _, _, (left, right), clock = make_drive()
    drive.update()                     # takes the starting counts
    left.value = right.value = 400     # one wheel revolution each
    clock.now += 0.5
    drive.update()
    odom = drive.odometry()
    assert (odom.x, odom.y, odom.theta) == pytest.approx((math.pi * 0.048, 0, 0))
    assert odom.linear == pytest.approx(math.pi * 0.048 / 0.5)
    assert odom.angular == pytest.approx(0)


def test_odometry_estimated_without_counters():
    drive, _, _, _, clock = make_drive(counters=False)
    drive.set_velocity(0.1, 0)
    drive.update()
    for _ in range(100):               # 2 s, keep commanding
        drive.set_velocity(0.1, 0)
        run(drive, clock, 0.02)
    odom = drive.odometry()
    assert odom.x == pytest.approx(0.2, abs=0.01)  # minus the ramp
    assert odom.linear == pytest.approx(0.1)


def test_counter_error_does_not_lose_pulses():
    drive, _, _, (left, right), clock = make_drive()
    drive.update()
    left.value = right.value = DeviceError('I2C failed')
    clock.now += 0.02
    with pytest.raises(DeviceError):
        drive.update()
    left.value = right.value = 400
    clock.now += 0.02
    drive.update()
    assert drive.odometry().x == pytest.approx(math.pi * 0.048)


def test_reset_odometry():
    drive, _, _, _, _ = make_drive()
    drive.reset_odometry(1.0, 2.0, 0.5)
    odom = drive.odometry()
    assert (odom.x, odom.y, odom.theta) == (1.0, 2.0, 0.5)


def test_needs_both_counters_or_neither():
    drive, motors, _, (left, _), _ = make_drive()
    with pytest.raises(ValueError):
        Drive(motors, CONFIG, left, None)


def test_close_stops_motors_at_once():
    drive, motors, pwms, _, clock = make_drive()
    drive.set_velocity(0.1, 0)
    drive.update()
    run(drive, clock, 0.3)
    drive.close()
    assert not pwms[0].running and not pwms[1].running
    assert drive.wheel_frequencies == (0, 0)
    drive.close()  # second close is allowed
    with pytest.raises(DeviceError):
        drive.set_velocity(0.1, 0)


def test_background_loop_starts_on_first_use_and_stops_on_close():
    pwms = (MockPwmChannel(), MockPwmChannel())
    motors = Motors(*(
        StepperMotor(pwm, MockDigitalOutput(ch.direction_pin), ch, MOTOR_CONFIG)
        for pwm, ch in zip(pwms, (MOTOR_CONFIG.left, MOTOR_CONFIG.right))))
    drive = Drive(motors, DriveConfig(control_rate_hz=200))
    assert drive._thread is None       # opening does not start it
    drive.set_velocity(0.1, 0)
    deadline = time.monotonic() + 2.0
    while pwms[0].frequency_hz == 0 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert pwms[0].frequency_hz > 0
    drive.close()
    assert not drive._thread.is_alive()
    assert not pwms[0].running
