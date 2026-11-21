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
