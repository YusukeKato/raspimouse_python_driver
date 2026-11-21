"""Push switches (SW1-SW3)."""

from ..hal.interfaces import DigitalInput


class Switch:
    """One push switch. Pulled up; the line reads low while pressed."""

    def __init__(self, line: DigitalInput) -> None:
        """Wrap a GPIO input line requested with pull-up bias."""
        self._line = line

    def is_pressed(self) -> bool:
        """Return True while the switch is pressed."""
        raise NotImplementedError

    def close(self) -> None:
        """Release the line."""
        raise NotImplementedError
