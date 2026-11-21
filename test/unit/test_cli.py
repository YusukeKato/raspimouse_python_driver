from raspimouse_python_driver.tools import cli


def test_led_turns_on_given_leds_then_off(lgpio, capsys):
    assert cli.main(['led', '0', '2', '--duration', '0']) == 0
    handle = lgpio.chip_handle
    assert ('gpio_write', handle, 25, 1) in lgpio.calls  # LED0
    assert ('gpio_write', handle, 23, 1) in lgpio.calls  # LED2
    assert ('gpio_write', handle, 24, 1) not in lgpio.calls  # LED1 stays off
    assert lgpio.calls[-1] == ('gpiochip_close', handle)
    assert 'LED 0 2 on' in capsys.readouterr().out


def test_led_defaults_to_all(lgpio):
    assert cli.main(['led', '--duration', '0']) == 0
    lit = [c[2] for c in lgpio.calls if c[0] == 'gpio_write' and c[3] == 1]
    assert lit == [25, 24, 23, 18]


def test_led_rejects_invalid_number(lgpio, capsys):
    assert cli.main(['led', '4', '--duration', '0']) == 2
    assert 'must be 0-3' in capsys.readouterr().err
    assert lgpio.calls == []


def test_device_error_is_reported(lgpio, capsys):
    lgpio.busy_pins.add(25)
    assert cli.main(['led', '--duration', '0']) == 1
    assert 'GPIO25' in capsys.readouterr().err
