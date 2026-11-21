"""Indicator LEDs (LED0-LED3)."""

from ..exceptions import DeviceError
from ..hal.interfaces import DigitalOutput


class Led:
    """One indicator LED. High = on."""

    def __init__(self, output: DigitalOutput) -> None:
        """Wrap a GPIO output line. The line should start low (off)."""
        self._output = output
        self._is_on = False
        self._closed = False

    def on(self) -> None:
        """Turn the LED on."""
        self.set_state(True)

    def off(self) -> None:
        """Turn the LED off."""
        self.set_state(False)

    def set_state(self, value: bool) -> None:
        """Turn the LED on (True) or off (False)."""
        if self._closed:
            raise DeviceError('LED is already closed')
        value = bool(value)
        self._output.write(value)
        self._is_on = value

    @property
    def is_on(self) -> bool:
        """Return the last commanded state."""
        return self._is_on

    def close(self) -> None:
        """Turn the LED off and release the line. Calling this more than once is allowed."""
        if self._closed:
            return
        try:
            self.off()
        finally:
            self._closed = True
            self._output.close()
