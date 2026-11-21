"""Buzzer."""

from ..config import BuzzerConfig
from ..hal.interfaces import PwmChannel


class Buzzer:
    """Buzzer driven by a square wave (software PWM)."""

    def __init__(self, pwm: PwmChannel, config: BuzzerConfig) -> None:
        """Wrap a PWM output."""
        self._pwm = pwm
        self._config = config

    def play(self, frequency_hz: int) -> None:
        """Sound at ``frequency_hz`` (clamped to 1 - max_frequency_hz). 0 stops."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop sounding."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop sounding and release resources."""
        raise NotImplementedError
