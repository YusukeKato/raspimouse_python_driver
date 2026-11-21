import os

import pytest

from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.linux.pwm import SysfsPwmChannel


def read(path):
    return path.read_text().strip()


@pytest.fixture
def writes(monkeypatch):
    """Record every sysfs write as (file name, value)."""
    log = []
    original = SysfsPwmChannel._write

    def recording(path, value):
        log.append((path.name, str(value)))
        original(path, value)
    monkeypatch.setattr(SysfsPwmChannel, '_write', staticmethod(recording))
    return log


def test_set_frequency_stop_close(sysfs_pwm):
    pwm = SysfsPwmChannel(0, 1)
    pwm0 = sysfs_pwm / 'pwm1'
    pwm.set_frequency(400)
    assert read(pwm0 / 'period') == '2500000'
    assert read(pwm0 / 'duty_cycle') == '1250000'
    assert read(pwm0 / 'enable') == '1'
    pwm.stop()
    assert read(pwm0 / 'enable') == '0'
    pwm.close()
    pwm.close()  # second close is allowed
    assert read(sysfs_pwm / 'unexport') == '1'
    with pytest.raises(DeviceError):
        pwm.set_frequency(400)


def test_init_stops_output_left_running(sysfs_pwm):
    (sysfs_pwm / 'pwm0' / 'period').write_text('2500000\n')
    (sysfs_pwm / 'pwm0' / 'enable').write_text('1\n')
    SysfsPwmChannel(0, 0)
    assert read(sysfs_pwm / 'pwm0' / 'enable') == '0'


def test_init_does_not_touch_fresh_channel(sysfs_pwm, writes):
    # Right after export the period is 0 and the kernel rejects writing
    # "enable" with EINVAL, so nothing may be written.
    SysfsPwmChannel(0, 0)
    assert writes == []


def test_duty_never_exceeds_period(sysfs_pwm, writes):
    pwm = SysfsPwmChannel(0, 0)
    pwm.set_frequency(100)    # period 10 ms, duty 5 ms
    writes.clear()
    pwm.set_frequency(1000)   # period 1 ms, duty 0.5 ms: duty must shrink first
    assert writes == [('duty_cycle', '500000'), ('period', '1000000')]
    writes.clear()
    pwm.set_frequency(100)    # period grows first
    assert writes == [('period', '10000000'), ('duty_cycle', '5000000')]
    writes.clear()
    pwm.set_frequency(100)    # unchanged: nothing written
    assert writes == []


def test_enable_written_once(sysfs_pwm, writes):
    pwm = SysfsPwmChannel(0, 0)
    pwm.set_frequency(100)
    pwm.set_frequency(200)
    assert [w for w in writes if w[0] == 'enable'] == [('enable', '1')]


def test_exports_missing_channel(tmp_path, make_sysfs_pwm):
    chip_dir = make_sysfs_pwm(tmp_path, exported=False)
    with pytest.raises(DeviceError, match='not writable'):
        SysfsPwmChannel(0, 1, root=tmp_path, timeout_s=0.05)
    assert read(chip_dir / 'export') == '1'


def test_missing_chip_mentions_overlay(tmp_path):
    with pytest.raises(DeviceError, match='pwm-2chan'):
        SysfsPwmChannel(0, 0, root=tmp_path)


@pytest.mark.skipif(os.geteuid() == 0, reason='root can write read-only files')
def test_not_writable(tmp_path, make_sysfs_pwm):
    chip_dir = make_sysfs_pwm(tmp_path)
    (chip_dir / 'pwm0' / 'enable').chmod(0o444)
    with pytest.raises(DeviceError, match='99-raspimouse-pwm.rules'):
        SysfsPwmChannel(0, 0, root=tmp_path, timeout_s=0.05)


@pytest.mark.parametrize('frequency, duty', [(0, 0.5), (2e6, 0.5), (400, 1.5), (400, -0.1)])
def test_out_of_range(sysfs_pwm, frequency, duty):
    pwm = SysfsPwmChannel(0, 0)
    with pytest.raises(ValueError):
        pwm.set_frequency(frequency, duty)
