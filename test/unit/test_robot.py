import pytest

from raspimouse_python_driver import RaspiMouse, RaspiMouseConfig
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockBackend, MockPwmChannel

LED_PINS = RaspiMouseConfig().led_pins


def test_open_creates_leds_on_configured_pins():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        assert len(mouse.leds) == 4
        assert set(RaspiMouseConfig().led_pins) <= set(backend.outputs)
        assert all(backend.outputs[pin].value is False for pin in LED_PINS)


def test_led_index_matches_pin_order():
    backend = MockBackend()
    with RaspiMouse(backend=backend) as mouse:
        mouse.leds[0].on()
        lit = [pin for pin in LED_PINS if backend.outputs[pin].value]
    assert lit == [LED_PINS[0]]


def test_close_turns_off_leds_and_closes_backend():
    backend = MockBackend()
    mouse = RaspiMouse(backend=backend)
    mouse.open()
    for led in mouse.leds:
        led.on()
    mouse.close()
    assert mouse.leds == ()
    assert backend.closed
    for pin in LED_PINS:
        assert backend.outputs[pin].value is False
    assert all(output.closed for output in backend.outputs.values())
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


def test_open_creates_light_sensors():
    backend = MockBackend()
    config = RaspiMouseConfig()
    with RaspiMouse(backend=backend) as mouse:
        sensors = config.light_sensors
        for name in ('right_front', 'right', 'left', 'left_front'):
            assert getattr(sensors, name).emitter_pin in backend.outputs
        spi = backend.spi_devices[(sensors.spi_bus, sensors.spi_chip_select)]
        assert mouse.light_sensors.read() == (0, 0, 0, 0)  # the mock SPI answers zeros
        assert len(spi.transfers) == 8  # 4 channels x (ambient, lit)
    assert mouse.light_sensors is None
    assert spi.closed


def test_open_creates_motors_unpowered():
    backend = MockBackend()
    config = RaspiMouseConfig().motors
    with RaspiMouse(backend=backend) as mouse:
        assert backend.outputs[config.enable_pin].value is False
        assert backend.outputs[config.left.direction_pin].value is config.left.forward_level
        assert backend.outputs[config.right.direction_pin].value is config.right.forward_level
        mouse.motor_power.on()
        mouse.motors.set_frequency(400, -400)
        left = backend.hardware_pwms[(config.pwm_chip, config.left.pwm_channel)]
        right = backend.hardware_pwms[(config.pwm_chip, config.right.pwm_channel)]
        assert left.frequency_hz == right.frequency_hz == 400
        assert backend.outputs[config.right.direction_pin].value is not config.right.forward_level
    # Leaving the block stops the motors and cuts the power.
    assert not left.running and not right.running
    assert left.closed and right.closed
    assert backend.outputs[config.enable_pin].value is False
    assert mouse.motors is None and mouse.motor_power is None


def test_motor_open_failure_closes_left_motor():
    backend = MockBackend()
    config = RaspiMouseConfig().motors
    # The right channel is already in use, so opening it fails.
    backend.hardware_pwms[(config.pwm_chip, config.right.pwm_channel)] = MockPwmChannel()
    with pytest.raises(DeviceError):
        RaspiMouse(backend=backend).open()
    assert backend.hardware_pwms[(config.pwm_chip, config.left.pwm_channel)].closed
    assert backend.closed
