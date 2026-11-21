"""GPIO through lgpio (GPIO character device)."""


class LgpioDigitalOutput:
    """GPIO output line."""

    def __init__(self, chip_handle: int, pin: int, initial: bool = False) -> None:
        """Claim ``pin`` as an output with the initial level."""
        raise NotImplementedError

    def write(self, value: bool) -> None:
        """Drive the line high (True) or low (False)."""
        raise NotImplementedError

    def close(self) -> None:
        """Free the line."""
        raise NotImplementedError


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
