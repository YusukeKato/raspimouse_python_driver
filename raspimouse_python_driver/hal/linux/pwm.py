"""
Hardware PWM through sysfs (``/sys/class/pwm/pwmchipN``).

The GPIO pins must be muxed to the PWM peripheral by a device tree overlay,
e.g. ``dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4`` (see config/).
Period and duty cycle are written in nanoseconds.
"""

from pathlib import Path

SYSFS_PWM_ROOT = Path('/sys/class/pwm')


class SysfsPwmChannel:
    """One channel of a sysfs PWM chip."""

    def __init__(self, chip: int, channel: int, root: Path = SYSFS_PWM_ROOT) -> None:
        """Export ``pwmchip{chip}/pwm{channel}`` if needed."""
        raise NotImplementedError

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """Start (or update) output with the given frequency and duty ratio."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop output."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop output and unexport the channel."""
        raise NotImplementedError
