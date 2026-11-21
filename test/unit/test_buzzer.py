import pytest

from raspimouse_python_driver.config import BuzzerConfig
from raspimouse_python_driver.devices.buzzer import Buzzer
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockPwmChannel


def make_buzzer():
    pwm = MockPwmChannel()
    return Buzzer(pwm, BuzzerConfig()), pwm


def test_play_and_stop():
    buzzer, pwm = make_buzzer()
    buzzer.play(440)
    assert (pwm.frequency_hz, pwm.duty_ratio) == (440, 0.5)
    assert buzzer.frequency_hz == 440
    buzzer.stop()
    assert not pwm.running
    assert buzzer.frequency_hz == 0


def test_play_zero_stops():
    buzzer, pwm = make_buzzer()
    buzzer.play(440)
    buzzer.play(0)
    assert not pwm.running


def test_frequency_is_clamped():
    buzzer, pwm = make_buzzer()
    buzzer.play(50_000)
    assert pwm.frequency_hz == BuzzerConfig().max_frequency_hz
    buzzer.play(0.2)
    assert pwm.frequency_hz == 1


def test_negative_frequency_raises():
    buzzer, _ = make_buzzer()
    with pytest.raises(ValueError):
        buzzer.play(-1)


def test_close_stops_and_releases():
    buzzer, pwm = make_buzzer()
    buzzer.play(440)
    buzzer.close()
    assert not pwm.running
    assert pwm.closed
    buzzer.close()  # second close is allowed
    with pytest.raises(DeviceError):
        buzzer.play(440)
