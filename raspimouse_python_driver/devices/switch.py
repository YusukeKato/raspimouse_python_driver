"""Push switches (switch 0-2)."""

from ..exceptions import DeviceError
from ..hal.interfaces import DigitalInput


class Switch:
    """One push switch. Pulled up; the line reads low while pressed."""

    def __init__(self, line: DigitalInput) -> None:
        """Wrap a GPIO input line requested with pull-up bias."""
        self._line = line
        self._closed = False

    def is_pressed(self) -> bool:
        """Return True while the switch is pressed."""
        if self._closed:
            raise DeviceError('switch is already closed')
        return not self._line.read()

    def close(self) -> None:
        """Release the line. Calling this more than once is allowed."""
        if self._closed:
            return
        self._closed = True
        self._line.close()
