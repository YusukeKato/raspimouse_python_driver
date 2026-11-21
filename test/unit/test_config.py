from raspimouse_python_driver import RaspiMouseConfig


def _all_gpio_pins(config):
    sensors = config.light_sensors
    motors = config.motors
    return [
        *config.led_pins,
        *config.switch_pins,
        sensors.right_front.emitter_pin,
        sensors.right.emitter_pin,
        sensors.left.emitter_pin,
        sensors.left_front.emitter_pin,
        motors.left.clock_pin,
        motors.left.direction_pin,
        motors.right.clock_pin,
        motors.right.direction_pin,
        motors.enable_pin,
        config.buzzer.pin,
    ]


def test_default_gpio_pins_are_unique():
    pins = _all_gpio_pins(RaspiMouseConfig())
    assert len(pins) == len(set(pins))


def test_default_adc_channels_cover_all_mcp3204_channels():
    sensors = RaspiMouseConfig().light_sensors
    channels = {
        sensors.right_front.adc_channel,
        sensors.right.adc_channel,
        sensors.left.adc_channel,
        sensors.left_front.adc_channel,
    }
    assert channels == {0, 1, 2, 3}


def test_device_counts():
    config = RaspiMouseConfig()
    assert len(config.led_pins) == 4
    assert len(config.switch_pins) == 3
