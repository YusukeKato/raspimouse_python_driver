import pytest

from raspimouse_python_driver.config import MotorConfig
from raspimouse_python_driver.devices.motor import MotorPower, Motors, StepperMotor
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockDigitalOutput, MockPwmChannel

CONFIG = MotorConfig()


def make_motor(channel=CONFIG.left):
    pwm = MockPwmChannel()
    direction = MockDigitalOutput(channel.direction_pin)
    return StepperMotor(pwm, direction, channel, CONFIG), pwm, direction


@pytest.mark.parametrize('channel', [CONFIG.left, CONFIG.right])
def test_direction_levels(channel):
    motor, pwm, direction = make_motor(channel)
    assert direction.value is channel.forward_level  # starts forward
    motor.set_frequency(400)
    assert direction.value is channel.forward_level
    assert motor.is_forward
    motor.set_frequency(-400)
    assert direction.value is (not channel.forward_level)
    assert not motor.is_forward
    assert (pwm.frequency_hz, pwm.duty_ratio) == (400, 0.5)
    assert motor.frequency_hz == -400


def test_left_and_right_forward_levels_match_rtmouse():
    # rtmouse: left forward = DIR low, right forward = DIR high.
    assert CONFIG.left.forward_level is False
    assert CONFIG.right.forward_level is True


def test_small_frequency_stops():
    motor, pwm, _ = make_motor()
    motor.set_frequency(400)
    motor.set_frequency(CONFIG.min_frequency_hz - 1)
    assert not pwm.running
    assert motor.frequency_hz == 0
    motor.set_frequency(-(CONFIG.min_frequency_hz - 1))
    assert not pwm.running


def test_frequency_is_clamped():
    motor, pwm, _ = make_motor()
    motor.set_frequency(-1_000_000)
    assert pwm.frequency_hz == CONFIG.max_frequency_hz
    assert motor.frequency_hz == -CONFIG.max_frequency_hz


def test_direction_is_not_rewritten_when_unchanged():
    motor, _, direction = make_motor()
    history = len(direction.history)
    motor.set_frequency(100)
    motor.set_frequency(200)
    assert len(direction.history) == history


def test_stop_and_close():
    motor, pwm, direction = make_motor()
    motor.set_frequency(400)
    motor.stop()
    assert not pwm.running
    motor.set_frequency(400)
    motor.close()
    assert not pwm.running
    assert pwm.closed and direction.closed
    motor.close()  # second close is allowed
    with pytest.raises(DeviceError):
        motor.set_frequency(400)


def test_motors_pair():
    left, left_pwm, _ = make_motor(CONFIG.left)
    right, right_pwm, _ = make_motor(CONFIG.right)
    motors = Motors(left, right)
    motors.set_frequency(100, -200)
    assert (left.frequency_hz, right.frequency_hz) == (100, -200)
    motors.stop()
    assert not left_pwm.running and not right_pwm.running
    motors.close()
    assert left_pwm.closed and right_pwm.closed


def test_motor_power():
    enable = MockDigitalOutput(5)
    power = MotorPower(enable)
    assert not power.is_on
    power.on()
    assert enable.value and power.is_on
    power.off()
    assert not enable.value and not power.is_on
    power.on()
    power.close()
    assert not enable.value and enable.closed
    power.close()  # second close is allowed
    with pytest.raises(DeviceError):
        power.on()


def test_direction_listener_runs_before_direction_changes():
    motor, _, direction = make_motor(CONFIG.right)
    seen = []
    motor.add_direction_change_listener(lambda: seen.append((motor.is_forward, direction.value)))
    motor.set_frequency(400)    # already forward: no call
    motor.set_frequency(-400)   # reversing: called with the old direction still set
    motor.set_frequency(-200)   # same direction: no call
    assert seen == [(True, CONFIG.right.forward_level)]


def test_failing_listener_does_not_stop_the_motor():
    motor, pwm, _ = make_motor()

    def broken():
        raise DeviceError('I2C failed')
    motor.add_direction_change_listener(broken)
    motor.set_frequency(-400)
    assert pwm.frequency_hz == 400
    assert not motor.is_forward
