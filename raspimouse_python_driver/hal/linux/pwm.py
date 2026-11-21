"""
Hardware PWM through sysfs (``/sys/class/pwm/pwmchipN``).

The GPIO pins must be muxed to the PWM peripheral by a device tree overlay,
e.g. ``dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`` (see config/).
Period and duty cycle are written in nanoseconds. Access without root needs
a udev rule (see config/99-raspimouse-pwm.rules).
"""

import os
from pathlib import Path
import time

from ...exceptions import DeviceError

SYSFS_PWM_ROOT = Path('/sys/class/pwm')
OVERLAY_HINT = 'is dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4 set in config.txt?'


class SysfsPwmChannel:
    """One channel of a sysfs PWM chip."""

    MIN_FREQUENCY_HZ = 0.1
    MAX_FREQUENCY_HZ = 1_000_000

    def __init__(self, chip: int, channel: int, root: Path | None = None,
                 timeout_s: float = 2.0) -> None:
        """
        Export ``pwmchip{chip}/pwm{channel}`` if needed and make sure it is stopped.

        :param root: sysfs PWM directory. Defaults to :data:`SYSFS_PWM_ROOT`.
        :param timeout_s: how long to wait for udev to set permissions after export.
        """
        chip_dir = Path(root if root is not None else SYSFS_PWM_ROOT) / f'pwmchip{chip}'
        self.path = chip_dir / f'pwm{channel}'
        if not chip_dir.is_dir():
            raise DeviceError(f'{chip_dir} not found: {OVERLAY_HINT}')
        if not self.path.is_dir():
            self._write(chip_dir / 'export', channel)
        self._wait_writable(timeout_s)
        self._closed = False
        # A previous process may have left the output running. Write "enable"
        # only then: the kernel rejects any change (even disabling) while the
        # period is 0, which is the state right after export.
        if self._read(self.path / 'enable'):
            self._write(self.path / 'enable', 0)
        self._enabled = False
        self._period_ns = self._read(self.path / 'period')
        self._duty_ns = self._read(self.path / 'duty_cycle')

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """
        Start (or update) output with the given frequency and duty ratio.

        :raises ValueError: frequency or duty ratio out of range.
        """
        self._check_open()
        if not self.MIN_FREQUENCY_HZ <= frequency_hz <= self.MAX_FREQUENCY_HZ:
            raise ValueError(
                f'frequency must be {self.MIN_FREQUENCY_HZ}-{self.MAX_FREQUENCY_HZ} Hz: '
                f'{frequency_hz}')
        if not 0.0 <= duty_ratio <= 1.0:
            raise ValueError(f'duty ratio must be 0.0-1.0: {duty_ratio}')
        period_ns = round(1e9 / frequency_hz)
        duty_ns = round(period_ns * duty_ratio)
        # The kernel rejects a duty cycle longer than the period at any moment,
        # so shrink the duty cycle first when the period gets shorter.
        if duty_ns < self._duty_ns or period_ns < self._duty_ns:
            self._set_duty(duty_ns)
            self._set_period(period_ns)
        else:
            self._set_period(period_ns)
            self._set_duty(duty_ns)
        if not self._enabled:
            self._write(self.path / 'enable', 1)
            self._enabled = True

    def stop(self) -> None:
        """Stop output."""
        self._check_open()
        if self._enabled:
            self._write(self.path / 'enable', 0)
            self._enabled = False

    def close(self) -> None:
        """Stop output and unexport the channel. Calling this more than once is allowed."""
        if self._closed:
            return
        try:
            self.stop()
        finally:
            self._closed = True
            try:
                self._write(self.path.parent / 'unexport', self.path.name[len('pwm'):])
            except DeviceError:
                pass

    def _set_period(self, period_ns: int) -> None:
        if period_ns != self._period_ns:
            self._write(self.path / 'period', period_ns)
            self._period_ns = period_ns

    def _set_duty(self, duty_ns: int) -> None:
        if duty_ns != self._duty_ns:
            self._write(self.path / 'duty_cycle', duty_ns)
            self._duty_ns = duty_ns

    def _wait_writable(self, timeout_s: float) -> None:
        deadline = time.monotonic() + timeout_s
        enable = self.path / 'enable'
        while not (enable.exists() and os.access(enable, os.W_OK)):
            if time.monotonic() > deadline:
                raise DeviceError(
                    f'{enable} is not writable: run as root or install '
                    'config/99-raspimouse-pwm.rules')
            time.sleep(0.01)

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError(f'{self.path} is already closed')

    @staticmethod
    def _write(path: Path, value) -> None:
        try:
            path.write_text(f'{value}\n')
        except OSError as e:
            raise DeviceError(f'cannot write {value} to {path}: {e}') from e

    @staticmethod
    def _read(path: Path) -> int:
        try:
            return int(path.read_text().strip())
        except (OSError, ValueError) as e:
            raise DeviceError(f'cannot read {path}: {e}') from e
