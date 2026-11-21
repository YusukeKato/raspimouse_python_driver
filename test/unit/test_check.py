import os

import pytest

from raspimouse_python_driver.tools import check
from raspimouse_python_driver.tools.check import FAIL, OK, run_checks, WARN

GOOD_CONFIG = """\
[all]
dtparam=i2c_arm=on
dtparam=spi=on
# Raspberry Pi Mouse V3 settings
dtparam=i2c_baudrate=62500
#dtoverlay=anyspi:spi0-0,dev="microchip,mcp3204",speed=1000000
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
"""


@pytest.fixture
def system(tmp_path, monkeypatch):
    """Create a fake root (/proc, /sys, /dev) and config.txt of a correctly set up robot."""
    root = tmp_path / 'root'
    (root / 'proc/device-tree').mkdir(parents=True)
    (root / 'proc/device-tree/model').write_bytes(b'Raspberry Pi 4 Model B Rev 1.5\x00')
    (root / 'sys/module').mkdir(parents=True)
    (root / 'dev').mkdir()
    for name in ('gpiochip0', 'spidev0.0', 'i2c-1'):
        (root / 'dev' / name).write_text('')
    pwm = root / 'sys/class/pwm/pwmchip0'
    pwm.mkdir(parents=True)
    (pwm / 'export').write_text('')
    config = tmp_path / 'config.txt'
    config.write_text(GOOD_CONFIG)
    monkeypatch.setattr(check, '_lgpio_installed', lambda: True)
    return root, config


def levels(results):
    return [r.level for r in results]


def problems(results):
    return [r for r in results if r.level != OK]


def test_good_setup_passes(system):
    root, config = system
    results = run_checks(root, config)
    assert problems(results) == []
    assert 'All checks passed.' in check.format_results(results)


def test_rtmouse_anyspi_overlay_is_reported_with_fix(system):
    root, config = system
    config.write_text(GOOD_CONFIG.replace('#dtoverlay=anyspi', 'dtoverlay=anyspi'))
    (found,) = problems(run_checks(root, config))
    assert found.level == FAIL
    assert 'anyspi' in found.message
    assert "sed -i 's/^dtoverlay=anyspi:spi0-0/#&/'" in found.fix
    assert 'reboot' in found.fix


def test_loaded_rtmouse_module_is_reported(system):
    root, config = system
    (root / 'sys/module/rtmouse').mkdir()
    (found,) = problems(run_checks(root, config))
    assert found.level == FAIL
    assert 'rmmod rtmouse' in found.fix


def test_missing_pwm_overlay_and_chip(system):
    root, config = system
    config.write_text(GOOD_CONFIG.replace('dtoverlay=pwm-2chan', '#dtoverlay=pwm-2chan'))
    (root / 'sys/class/pwm/pwmchip0/export').unlink()
    (root / 'sys/class/pwm/pwmchip0').rmdir()
    found = problems(run_checks(root, config))
    assert levels(found) == [FAIL, FAIL]
    assert all('pwm-2chan' in r.fix for r in found)


def test_missing_spi_and_i2c_settings(system):
    root, config = system
    config.write_text('dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4\n')
    messages = [r.message for r in problems(run_checks(root, config))]
    assert any('dtparam=spi=on' in m for m in messages)
    assert any('dtparam=i2c_arm=on' in m for m in messages)
    assert any('i2c_baudrate' in m for m in messages)


def test_baudrate_is_only_a_warning(system):
    root, config = system
    config.write_text(GOOD_CONFIG.replace('dtparam=i2c_baudrate=62500', ''))
    assert levels(problems(run_checks(root, config))) == [WARN]


def test_missing_device_file(system):
    root, config = system
    (root / 'dev/spidev0.0').unlink()
    (found,) = problems(run_checks(root, config))
    assert '/dev/spidev0.0' in found.message
    assert 'anyspi' in found.fix


@pytest.mark.skipif(os.geteuid() == 0, reason='root can access anything')
def test_permissions(system):
    root, config = system
    (root / 'dev/gpiochip0').chmod(0o000)
    (root / 'sys/class/pwm/pwmchip0/export').chmod(0o444)
    fixes = [r.fix for r in problems(run_checks(root, config))]
    assert any('usermod -aG dialout' in f for f in fixes)
    assert any('99-raspimouse-pwm.rules' in f for f in fixes)


def test_lgpio_missing(system, monkeypatch):
    root, config = system
    monkeypatch.setattr(check, '_lgpio_installed', lambda: False)
    (found,) = problems(run_checks(root, config))
    assert 'apt install python3-lgpio' in found.fix


def test_not_raspberry_pi4(system):
    root, config = system
    (root / 'proc/device-tree/model').write_bytes(b'Raspberry Pi 5 Model B Rev 1.0\x00')
    (found,) = problems(run_checks(root, config))
    assert 'Raspberry Pi 4' in found.fix


def test_format_shows_fixes_and_summary(system):
    root, config = system
    (root / 'sys/module/rtmouse').mkdir()
    text = check.format_results(run_checks(root, config))
    assert '[FAIL] the rtmouse kernel module is loaded' in text
    assert '       sudo rmmod rtmouse' in text
    assert '1 problem(s), 0 warning(s)' in text
