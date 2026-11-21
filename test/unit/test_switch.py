import pytest

from raspimouse_python_driver.devices.switch import Switch
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockDigitalInput


def test_pressed_when_line_is_low():
    line = MockDigitalInput(20, pull_up=True)
    switch = Switch(line)
    assert not switch.is_pressed()  # pulled up = released
    line.level = False
    assert switch.is_pressed()
    line.level = True
    assert not switch.is_pressed()


def test_close_releases_line():
    line = MockDigitalInput(20, pull_up=True)
    switch = Switch(line)
    switch.close()
    assert line.closed
    switch.close()  # second close is allowed


def test_use_after_close_raises():
    switch = Switch(MockDigitalInput(20, pull_up=True))
    switch.close()
    with pytest.raises(DeviceError):
        switch.is_pressed()
