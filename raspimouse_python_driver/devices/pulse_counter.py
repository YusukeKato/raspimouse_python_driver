"""Pulse counters of Raspberry Pi Mouse V3 (I2C)."""

from collections.abc import Callable
import threading

from ..config import PulseCounterConfig
from ..exceptions import DeviceError
from ..hal.interfaces import I2cDevice


class PulseCounter:
    """
    Counts step pulses sent to one motor.

    The hardware counter is unsigned 16 bit and counts up regardless of the
    rotation direction. :meth:`read_signed` accumulates the increments with
    the sign given by ``is_forward`` and handles the wrap-around of the raw
    counter. Call :meth:`update` right before the direction changes so that
    earlier pulses are counted with the old direction (RaspiMouse does this).
    The signed count starts at 0 when the counter is created. Thread safe.

    Update at least every 3 s at full speed (10 kHz), or wraps of the 16 bit
    counter are miscounted.
    """

    MAX_RAW = 0xFFFF
    _RANGE = MAX_RAW + 1

    def __init__(self, i2c: I2cDevice, config: PulseCounterConfig,
                 is_forward: Callable[[], bool]) -> None:
        """
        Wrap the I2C counter device and take the current count as the start.

        :param i2c: I2C device of this counter.
        :param config: register addresses.
        :param is_forward: returns the current rotation direction of the motor.
        :raises DeviceError: the counter does not answer (it exists on V3 only).
        """
        self._i2c = i2c
        self._config = config
        self._is_forward = is_forward
        self._lock = threading.Lock()
        self._closed = False
        self._last_raw = self._read_raw()
        self._signed = 0

    def read_raw(self) -> int:
        """Return the raw unsigned 16 bit count."""
        with self._lock:
            self._check_open()
            return self._read_raw()

    def update(self) -> None:
        """Add the pulses since the last update with the current direction."""
        with self._lock:
            self._check_open()
            self._update()

    def read_signed(self) -> int:
        """Return the signed count: forward pulses minus backward pulses."""
        with self._lock:
            self._check_open()
            self._update()
            return self._signed

    def reset(self, value: int = 0) -> None:
        """Set the signed count to ``value``. The hardware counter is not changed."""
        with self._lock:
            self._check_open()
            self._last_raw = self._read_raw()
            self._signed = value

    def close(self) -> None:
        """Close the I2C device. Calling this more than once is allowed."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._i2c.close()

    def _update(self) -> None:
        raw = self._read_raw()
        # The counter only counts up, but take the difference as signed so that
        # a bad reading is undone by the next one instead of adding ~65000
        # pulses. Wraps of the counter (0xFFFF -> 0) are handled the same way.
        increment = self._difference(raw, self._last_raw)
        self._last_raw = raw
        self._signed += increment if self._is_forward() else -increment

    def _read_raw(self) -> int:
        # Same order as rtmouse: LSB first, then MSB. The two bytes come from
        # separate I2C transfers, but the counter firmware keeps them
        # consistent: with 5 kHz pulses (an LSB carry every 51 ms) and about
        # 0.7 ms between the two transfers, about 1700 readings per counter
        # gave no value off by 256, where about 24 were expected otherwise
        # (issue #2). The signed difference in _update() guards against a bad
        # reading anyway.
        lsb = self._i2c.read_byte_data(self._config.lsb_register)
        msb = self._i2c.read_byte_data(self._config.msb_register)
        return ((msb & 0xFF) << 8) | (lsb & 0xFF)

    @classmethod
    def _difference(cls, raw: int, previous: int) -> int:
        """Return ``raw - previous`` as -32768..32767, across the 16 bit wrap."""
        return (raw - previous + cls._RANGE // 2) % cls._RANGE - cls._RANGE // 2

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError('pulse counter is already closed')
