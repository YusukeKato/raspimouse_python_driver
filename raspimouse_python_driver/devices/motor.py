"""Stepper motors and motor power."""

from ..config import MotorChannelConfig, MotorConfig
from ..hal.interfaces import DigitalOutput, PwmChannel


class StepperMotor:
    """
    One stepper motor driven by step pulses (PWM) and a direction pin.

    The signed frequency [Hz] selects speed and direction: positive is forward.
    Values whose absolute value is below ``min_frequency_hz`` stop the motor,
    and values above ``max_frequency_hz`` are clamped.
    """

    def __init__(self, pwm: PwmChannel, direction: DigitalOutput,
                 channel: MotorChannelConfig, config: MotorConfig) -> None:
        """Wrap the PWM channel and the direction line of one motor."""
        self._pwm = pwm
        self._direction = direction
        self._channel = channel
        self._config = config

    def set_frequency(self, frequency_hz: int) -> None:
        """Set the signed step frequency [Hz]."""
        raise NotImplementedError

    @property
    def frequency_hz(self) -> int:
        """Return the last applied signed frequency (0 when stopped)."""
        raise NotImplementedError

    @property
    def is_forward(self) -> bool:
        """Return True if the last applied direction is forward."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop step pulses."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop and release resources."""
        raise NotImplementedError


class Motors:
    """The left and right motors."""

    def __init__(self, left: StepperMotor, right: StepperMotor) -> None:
        """Bundle the two motors."""
        self.left = left
        self.right = right

    def set_frequency(self, left: int, right: int) -> None:
        """Set the signed step frequencies [Hz] of both motors."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop both motors."""
        raise NotImplementedError

    def close(self) -> None:
        """Stop both motors and release resources."""
        raise NotImplementedError


class MotorPower:
    """Motor power (enable) shared by both motor drivers. High = powered."""

    def __init__(self, enable: DigitalOutput) -> None:
        """Wrap the enable line."""
        self._enable = enable

    def on(self) -> None:
        """Power the motors (they hold their position)."""
        raise NotImplementedError

    def off(self) -> None:
        """Cut motor power."""
        raise NotImplementedError

    @property
    def is_on(self) -> bool:
        """Return the last commanded state."""
        raise NotImplementedError

    def close(self) -> None:
        """Cut motor power and release the line."""
        raise NotImplementedError
