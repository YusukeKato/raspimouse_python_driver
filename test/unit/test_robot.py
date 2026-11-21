from raspimouse_python_driver import RaspiMouse, RaspiMouseConfig
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
