"""GPIO through lgpio (GPIO character device)."""

from ._lgpio import import_lgpio
from ...exceptions import DeviceError


class LgpioDigitalOutput:
    """GPIO output line."""

    def __init__(self, chip_handle: int, pin: int, initial: bool = False) -> None:
        """Claim ``pin`` as an output with the initial level."""
        self._lgpio = import_lgpio()
        self._chip_handle = chip_handle
        self.pin = pin
        try:
            self._lgpio.gpio_claim_output(chip_handle, pin, int(bool(initial)))
        except self._lgpio.error as e:
            raise DeviceError(f'cannot claim GPIO{pin} as output: {e}') from e
        self._closed = False

    def write(self, value: bool) -> None:
        """Drive the line high (True) or low (False)."""
        if self._closed:
            raise DeviceError(f'GPIO{self.pin} is already closed')
        try:
            self._lgpio.gpio_write(self._chip_handle, self.pin, int(bool(value)))
        except self._lgpio.error as e:
            raise DeviceError(f'cannot write GPIO{self.pin}: {e}') from e

    def close(self) -> None:
        """Free the line. Calling this more than once is allowed."""
        if self._closed:
            return
        self._closed = True
        try:
            self._lgpio.gpio_free(self._chip_handle, self.pin)
        except self._lgpio.error:
            # The line is freed anyway when the chip is closed.
            pass


class LgpioDigitalInput:
    """GPIO input line."""

    def __init__(self, chip_handle: int, pin: int, pull_up: bool = False) -> None:
        """Claim ``pin`` as an input, optionally with pull-up bias."""
        raise NotImplementedError

    def read(self) -> bool:
        """Return the current level of the line."""
        raise NotImplementedError

    def close(self) -> None:
        """Free the line."""
        raise NotImplementedError


class LgpioSoftwarePwm:
    """
    Software timed PWM on any GPIO (lgpio ``tx_pwm``).

    Accurate enough for the buzzer, but not for the stepper motors, which use
    hardware PWM (:class:`~.pwm.SysfsPwmChannel`). lgpio limits the frequency
    to 10 kHz.
    """

    def __init__(self, chip_handle: int, pin: int) -> None:
        """Claim ``pin`` as an output used for PWM."""
        raise NotImplementedError

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """Start (or update) output with the given frequency and duty ratio."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop output and drive the line low."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop output and free the line."""
        raise NotImplementedError
