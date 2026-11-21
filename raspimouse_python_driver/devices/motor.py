"""Stepper motors and motor power."""

from collections.abc import Callable
import logging
import threading

from ..config import MotorChannelConfig, MotorConfig
from ..exceptions import DeviceError
from ..hal.interfaces import DigitalOutput, PwmChannel

_logger = logging.getLogger(__name__)


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
        self._frequency_hz: float = 0
        self._is_forward = True
        self._lock = threading.Lock()
        self._closed = False
        self._direction_listeners: list[Callable[[], None]] = []
        self._direction.write(channel.forward_level)

    def add_direction_change_listener(self, callback: Callable[[], None]) -> None:
        """
        Call ``callback`` right before the rotation direction changes.

        Used by the pulse counter to count earlier pulses with the old
        direction. Errors in ``callback`` are logged and do not stop the motor
        command.
        """
        self._direction_listeners.append(callback)

    def set_frequency(self, frequency_hz: float) -> None:
        """Set the signed step frequency [Hz]."""
        with self._lock:
            self._check_open()
            magnitude = abs(frequency_hz)
            if magnitude < self._config.min_frequency_hz:
                self._stop()
                return
            magnitude = min(magnitude, self._config.max_frequency_hz)
            forward = frequency_hz > 0
            if forward != self._is_forward:
                for callback in self._direction_listeners:
                    try:
                        callback()
                    except Exception:
                        _logger.warning('direction change listener failed', exc_info=True)
                # forward_level is the level for forward; backward is the opposite.
                self._direction.write(self._channel.forward_level == forward)
                self._is_forward = forward
            self._pwm.set_frequency(magnitude, 0.5)
            self._frequency_hz = magnitude if forward else -magnitude

    @property
    def frequency_hz(self) -> float:
        """Return the last applied signed frequency (0 when stopped)."""
        return self._frequency_hz

    @property
    def is_forward(self) -> bool:
        """Return True if the last applied direction is forward."""
        return self._is_forward

    def stop(self) -> None:
        """Stop step pulses."""
        with self._lock:
            self._check_open()
            self._stop()

    def close(self) -> None:
        """Stop and release resources. Calling this more than once is allowed."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._stop()
            finally:
                try:
                    self._pwm.close()
                finally:
                    self._direction.close()

    def _stop(self) -> None:
        self._pwm.stop()
        self._frequency_hz = 0

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError('motor is already closed')


class Motors:
    """The left and right motors."""

    def __init__(self, left: StepperMotor, right: StepperMotor) -> None:
        """Bundle the two motors."""
        self.left = left
        self.right = right

    def set_frequency(self, left: float, right: float) -> None:
        """Set the signed step frequencies [Hz] of both motors."""
        self.left.set_frequency(left)
        self.right.set_frequency(right)

    def stop(self) -> None:
        """Stop both motors (the right one is stopped even if the left one fails)."""
        try:
            self.left.stop()
        finally:
            self.right.stop()

    def close(self) -> None:
        """Stop both motors and release resources."""
        try:
            self.left.close()
        finally:
            self.right.close()


class MotorPower:
    """
    Motor power (enable) shared by both motor drivers. High = powered.

    While powered, the motors hold their position even when stopped.
    """

    def __init__(self, enable: DigitalOutput) -> None:
        """Wrap the enable line. The line should start low (off)."""
        self._enable = enable
        self._is_on = False
        self._closed = False

    def on(self) -> None:
        """Power the motors."""
        self._set(True)

    def off(self) -> None:
        """Cut motor power."""
        self._set(False)

    @property
    def is_on(self) -> bool:
        """Return the last commanded state."""
        return self._is_on

    def close(self) -> None:
        """Cut motor power and release the line. Calling this more than once is allowed."""
        if self._closed:
            return
        try:
            self.off()
        finally:
            self._closed = True
            self._enable.close()

    def _set(self, value: bool) -> None:
        if self._closed:
            raise DeviceError('motor power is already closed')
        self._enable.write(value)
        self._is_on = value
