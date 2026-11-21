import pytest

from raspimouse_python_driver.devices.led import Led
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockDigitalOutput


def test_on_and_off():
    output = MockDigitalOutput(25)
    led = Led(output)
    assert not led.is_on

    led.on()
    assert output.value is True
    assert led.is_on

    led.off()
    assert output.value is False
    assert not led.is_on


def test_set_state():
    output = MockDigitalOutput(25)
    led = Led(output)
    led.set_state(True)
    led.set_state(False)
    led.set_state(1)
    assert output.history == [False, True, False, True]


def test_close_turns_off_and_releases_line():
    output = MockDigitalOutput(25)
    led = Led(output)
    led.on()
    led.close()
    assert output.value is False
    assert output.closed
    led.close()  # second close is allowed


def test_use_after_close_raises():
    led = Led(MockDigitalOutput(25))
    led.close()
    with pytest.raises(DeviceError):
        led.on()
