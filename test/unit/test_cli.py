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


def test_switch_prints_states_once(lgpio, capsys):
    lgpio.levels[21] = 0  # switch 2 pressed
    assert cli.main(['switch']) == 0
    out = capsys.readouterr().out
    assert out.count('\n') == 1
    assert '0: released, 1: released, 2: pressed' in out
    assert lgpio.calls[-1] == ('gpiochip_close', lgpio.chip_handle)


def test_switch_watch_ends_after_duration(lgpio, capsys):
    assert cli.main(['switch', '--watch', '--duration', '0']) == 0
    assert '0: released, 1: released, 2: released' in capsys.readouterr().out


def test_buzzer_plays_frequencies_in_order(lgpio, capsys):
    assert cli.main(['buzzer', '440', '0', '880', '--duration', '0']) == 0
    tx = [c[3:] for c in lgpio.calls if c[0] == 'tx_pwm']
    assert tx[0] == (440, 50.0)
    assert tx[1] == (0, 0)  # rest
    assert tx[2] == (880, 50.0)
    assert tx[-1] == (0, 0)
    out = capsys.readouterr().out
    assert '440 Hz' in out and '880 Hz' in out


def test_buzzer_rejects_negative(lgpio, capsys):
    assert cli.main(['buzzer', '--duration', '0', '--', '-5']) == 2
    assert 'must not be negative' in capsys.readouterr().err
    assert lgpio.calls == []


def test_sensor_prints_values_once(lgpio, capsys):
    assert cli.main(['sensor']) == 0
    out = capsys.readouterr().out
    assert out.count('\n') == 1
    assert 'RF     0  R     0  L     0  LF     0' in out
    assert ('spi_close', lgpio.spi_handle) in lgpio.calls
