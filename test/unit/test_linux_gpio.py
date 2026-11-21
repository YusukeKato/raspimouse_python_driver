"""Tests of the lgpio backend with a fake lgpio module (no hardware needed)."""

import pytest

from raspimouse_python_driver import RaspiMouse
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.linux import LinuxBackend


def test_digital_output_claim_write_free(lgpio):
    backend = LinuxBackend(gpio_chip=0)
    output = backend.digital_output(25, initial=False)
    output.write(True)
    output.write(False)
    output.close()
    output.close()  # second close is allowed
    backend.close()
    assert lgpio.calls == [
        ('gpiochip_open', 0),
        ('gpio_claim_output', lgpio.chip_handle, 25, 0),
        ('gpio_write', lgpio.chip_handle, 25, 1),
        ('gpio_write', lgpio.chip_handle, 25, 0),
        ('gpio_free', lgpio.chip_handle, 25),
        ('gpiochip_close', lgpio.chip_handle),
    ]


def test_chip_is_opened_once(lgpio):
    backend = LinuxBackend()
    backend.digital_output(25)
    backend.digital_output(24)
    assert [c for c in lgpio.calls if c[0] == 'gpiochip_open'] == [('gpiochip_open', 0)]


def test_claim_failure_raises_device_error(lgpio):
    lgpio.busy_pins.add(25)
    with pytest.raises(DeviceError, match='GPIO25'):
        LinuxBackend().digital_output(25)


def test_write_after_close_raises(lgpio):
    output = LinuxBackend().digital_output(25)
    output.close()
    with pytest.raises(DeviceError):
        output.write(True)


def test_raspimouse_leds_through_lgpio(lgpio):
    with RaspiMouse() as mouse:
        mouse.leds[0].on()
    claimed = [c[2] for c in lgpio.calls if c[0] == 'gpio_claim_output']
    freed = [c[2] for c in lgpio.calls if c[0] == 'gpio_free']
    assert claimed == [25, 24, 23, 18]
    assert sorted(freed) == sorted(claimed)
    assert ('gpio_write', lgpio.chip_handle, 25, 1) in lgpio.calls
    # LED0 is turned off before it is freed.
    assert lgpio.calls.index(('gpio_write', lgpio.chip_handle, 25, 0)) < \
        lgpio.calls.index(('gpio_free', lgpio.chip_handle, 25))
    assert lgpio.calls[-1] == ('gpiochip_close', lgpio.chip_handle)
