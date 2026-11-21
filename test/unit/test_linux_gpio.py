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
    outputs = [c[2] for c in lgpio.calls if c[0] == 'gpio_claim_output']
    inputs = [c[2] for c in lgpio.calls if c[0] == 'gpio_claim_input']
    freed = [c[2] for c in lgpio.calls if c[0] == 'gpio_free']
    assert outputs == [25, 24, 23, 18, 19]  # LEDs and the buzzer
    assert inputs == [20, 26, 21]
    assert sorted(freed) == sorted(outputs + inputs)
    assert ('gpio_write', lgpio.chip_handle, 25, 1) in lgpio.calls
    # LED0 is turned off before it is freed.
    assert lgpio.calls.index(('gpio_write', lgpio.chip_handle, 25, 0)) < \
        lgpio.calls.index(('gpio_free', lgpio.chip_handle, 25))
    assert lgpio.calls[-1] == ('gpiochip_close', lgpio.chip_handle)


def test_digital_input_with_pull_up(lgpio):
    backend = LinuxBackend()
    line = backend.digital_input(20, pull_up=True)
    assert ('gpio_claim_input', lgpio.chip_handle, 20, lgpio.SET_PULL_UP) in lgpio.calls
    lgpio.levels[20] = 1
    assert line.read() is True
    lgpio.levels[20] = 0
    assert line.read() is False
    line.close()
    assert ('gpio_free', lgpio.chip_handle, 20) in lgpio.calls
    with pytest.raises(DeviceError):
        line.read()


def test_digital_input_without_pull_up(lgpio):
    LinuxBackend().digital_input(20)
    assert ('gpio_claim_input', lgpio.chip_handle, 20, 0) in lgpio.calls


def test_input_claim_failure_raises_device_error(lgpio):
    lgpio.busy_pins.add(26)
    with pytest.raises(DeviceError, match='GPIO26'):
        LinuxBackend().digital_input(26, pull_up=True)


def test_raspimouse_switches_through_lgpio(lgpio):
    lgpio.levels[26] = 0  # switch 1 pressed
    with RaspiMouse() as mouse:
        assert [sw.is_pressed() for sw in mouse.switches] == [False, True, False]


def test_software_pwm(lgpio):
    backend = LinuxBackend()
    pwm = backend.software_pwm(19)
    handle = lgpio.chip_handle
    assert ('gpio_claim_output', handle, 19, 0) in lgpio.calls
    pwm.set_frequency(440, 0.5)
    pwm.stop()
    pwm.close()
    pwm.close()  # second close is allowed
    pwm_calls = [c for c in lgpio.calls if c[0] in ('tx_pwm', 'gpio_free')]
    assert pwm_calls == [
        ('tx_pwm', handle, 19, 440, 50.0),
        ('tx_pwm', handle, 19, 0, 0),
        ('gpio_free', handle, 19),  # already stopped, so no second "off"
    ]


def test_software_pwm_close_while_running_stops_first(lgpio):
    pwm = LinuxBackend().software_pwm(19)
    pwm.set_frequency(440)
    pwm.close()
    pwm_calls = [c[0:1] + c[3:] for c in lgpio.calls if c[0] in ('tx_pwm', 'gpio_free')]
    assert pwm_calls == [('tx_pwm', 440, 50.0), ('tx_pwm', 0, 0), ('gpio_free',)]


def test_software_pwm_stop_without_start_is_noop(lgpio):
    pwm = LinuxBackend().software_pwm(19)
    pwm.stop()
    pwm.stop()
    pwm.close()
    assert not [c for c in lgpio.calls if c[0] == 'tx_pwm']


def test_raspimouse_close_without_using_buzzer(lgpio):
    with RaspiMouse():
        pass
    assert lgpio.calls[-1] == ('gpiochip_close', lgpio.chip_handle)


@pytest.mark.parametrize('frequency, duty', [(0, 0.5), (10_001, 0.5), (440, 1.5), (440, -0.1)])
def test_software_pwm_rejects_out_of_range(lgpio, frequency, duty):
    pwm = LinuxBackend().software_pwm(19)
    with pytest.raises(ValueError):
        pwm.set_frequency(frequency, duty)


def test_raspimouse_buzzer_through_lgpio(lgpio):
    with RaspiMouse() as mouse:
        mouse.buzzer.play(880)
    tx = [c[3:] for c in lgpio.calls if c[0] == 'tx_pwm']
    assert tx[0] == (880, 50.0)
    assert tx[-1] == (0, 0)  # stopped on close
