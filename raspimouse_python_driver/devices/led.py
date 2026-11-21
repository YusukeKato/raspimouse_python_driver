"""Indicator LEDs (LED0-LED3)."""

from ..hal.interfaces import DigitalOutput


class Led:
    """One indicator LED. High = on."""

    def __init__(self, output: DigitalOutput) -> None:
        """Wrap a GPIO output line."""
        self._output = output

    def on(self) -> None:
        """Turn the LED on."""
        raise NotImplementedError

    def off(self) -> None:
        """Turn the LED off."""
        raise NotImplementedError

    def set_state(self, value: bool) -> None:
        """Turn the LED on (True) or off (False)."""
        raise NotImplementedError

    @property
    def is_on(self) -> bool:
        """Return the last commanded state."""
        raise NotImplementedError

    def close(self) -> None:
        """Turn the LED off and release the line."""
        raise NotImplementedError
