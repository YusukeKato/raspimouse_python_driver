"""Buzzer."""

from ..config import BuzzerConfig
from ..exceptions import DeviceError
from ..hal.interfaces import PwmChannel


class Buzzer:
    """Buzzer driven by a square wave (software PWM)."""

    MIN_FREQUENCY_HZ = 1

    def __init__(self, pwm: PwmChannel, config: BuzzerConfig) -> None:
        """Wrap a PWM output."""
        self._pwm = pwm
        self._config = config
        self._frequency_hz: float = 0
        self._closed = False

    def play(self, frequency_hz: float) -> None:
        """
        Sound at ``frequency_hz`` [Hz]. 0 stops.

        Values are clamped to 1 - ``max_frequency_hz`` of the configuration.

        :raises ValueError: ``frequency_hz`` is negative.
        """
        self._check_open()
        if frequency_hz < 0:
            raise ValueError(f'frequency must not be negative: {frequency_hz}')
        if frequency_hz == 0:
            self.stop()
            return
        frequency_hz = min(max(frequency_hz, self.MIN_FREQUENCY_HZ),
                           self._config.max_frequency_hz)
        self._pwm.set_frequency(frequency_hz, 0.5)
        self._frequency_hz = frequency_hz

    def stop(self) -> None:
        """Stop sounding."""
        self._check_open()
        self._pwm.stop()
        self._frequency_hz = 0

    @property
    def frequency_hz(self) -> float:
        """Return the current frequency [Hz] (0 when silent)."""
        return self._frequency_hz

    def close(self) -> None:
        """Stop sounding and release resources. Calling this more than once is allowed."""
        if self._closed:
            return
        try:
            self.stop()
        finally:
            self._closed = True
            self._pwm.close()

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError('buzzer is already closed')
