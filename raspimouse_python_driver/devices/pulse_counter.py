"""Pulse counters of Raspberry Pi Mouse V3 (I2C)."""

from collections.abc import Callable

from ..config import PulseCounterConfig
from ..hal.interfaces import I2cDevice


class PulseCounter:
    """
    Counts step pulses sent to one motor.

    The hardware counter is unsigned 16 bit and counts up regardless of the
    rotation direction. :meth:`read_signed` accumulates the differences with
    the sign given by ``is_forward`` and handles the wrap-around of the raw
    counter.
    """

    MAX_RAW = 0xFFFF

    def __init__(self, i2c: I2cDevice, config: PulseCounterConfig,
                 is_forward: Callable[[], bool]) -> None:
        """
        Wrap the I2C counter device.

        :param i2c: I2C device of this counter.
        :param config: register addresses.
        :param is_forward: returns the current rotation direction of the motor.
        """
        self._i2c = i2c
        self._config = config
        self._is_forward = is_forward

    def read_raw(self) -> int:
        """Return the raw unsigned 16 bit count."""
        raise NotImplementedError

    def read_signed(self) -> int:
        """Return the signed count accumulated with the rotation direction."""
        raise NotImplementedError

    def reset(self, value: int = 0) -> None:
        """Set the hardware counter and the signed count to ``value``."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the I2C device."""
        raise NotImplementedError
