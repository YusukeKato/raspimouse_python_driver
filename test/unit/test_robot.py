import pytest

from raspimouse_python_driver import RaspiMouse, RaspiMouseConfig
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockBackend


def test_open_creates_leds_on_configured_pins():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        assert len(mouse.leds) == 4
        assert set(backend.outputs) == set(RaspiMouseConfig().led_pins)
        assert all(output.value is False for output in backend.outputs.values())


def test_led_index_matches_pin_order():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        mouse.leds[0].on()
        lit = [pin for pin, output in backend.outputs.items() if output.value]
    assert lit == [RaspiMouseConfig().led_pins[0]]


def test_close_turns_off_leds_and_closes_backend():
    backend = MockBackend()
    mouse = RaspiMouse(backend=backend)
    mouse.open()
    for led in mouse.leds:
        led.on()
    mouse.close()
    assert mouse.leds == ()
    assert backend.closed
    for output in backend.outputs.values():
        assert output.value is False
        assert output.closed
    mouse.close()  # second close is allowed


def test_open_twice_and_reopen():
    backend = MockBackend()
    mouse = RaspiMouse(backend=backend)
    mouse.open()
    mouse.open()  # no-op, does not claim the pins twice
    mouse.close()
    mouse.open()  # can be opened again after close
    assert len(mouse.leds) == 4
    mouse.close()


def test_open_creates_switches_with_pull_up():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        assert len(mouse.switches) == 3
        assert list(backend.inputs) == list(RaspiMouseConfig().switch_pins)
        assert all(line.pull_up for line in backend.inputs.values())
        backend.inputs[RaspiMouseConfig().switch_pins[2]].level = False
        assert [sw.is_pressed() for sw in mouse.switches] == [False, False, True]
    assert mouse.switches == ()
    assert all(line.closed for line in backend.inputs.values())


def test_open_creates_buzzer_and_close_stops_it():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        mouse.buzzer.play(440)
        pwm = backend.software_pwms[RaspiMouseConfig().buzzer.pin]
        assert pwm.frequency_hz == 440
    assert mouse.buzzer is None
    assert not pwm.running
    assert pwm.closed


def test_close_continues_after_a_device_error():
    backend = MockBackend()
    mouse = RaspiMouse(backend=backend)
    mouse.open()
    backend.software_pwms[RaspiMouseConfig().buzzer.pin].closed = True  # makes stop() fail
    with pytest.raises(DeviceError):
        mouse.close()
    # The other devices and the backend are still released.
    assert all(output.closed for output in backend.outputs.values())
    assert all(line.closed for line in backend.inputs.values())
    assert backend.closed
