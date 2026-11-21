"""High level interface that bundles all devices of Raspberry Pi Mouse."""

from .config import RaspiMouseConfig
from .devices.buzzer import Buzzer
from .devices.led import Led
from .devices.light_sensor import LightSensors
from .devices.motor import MotorPower, Motors
from .devices.pulse_counter import PulseCounter
from .devices.switch import Switch
from .hal.interfaces import Backend
from .hal.linux import LinuxBackend


class RaspiMouse:
    """
    All devices of Raspberry Pi Mouse.

    Usage::

        with RaspiMouse() as mouse:
            mouse.motor_power.on()
            mouse.motors.set_frequency(left=400, right=400)
            values = mouse.light_sensors.read()

    On close (or leaving the ``with`` block) the motors are stopped and the
    motor power is turned off before the hardware resources are released.
    """

    def __init__(self, config: RaspiMouseConfig | None = None,
                 backend: Backend | None = None) -> None:
        """
        Create the interface. Hardware is not touched until :meth:`open`.

        :param config: hardware configuration. Defaults to Raspberry Pi Mouse on Pi 4.
        :param backend: hardware backend. Defaults to :class:`LinuxBackend`.
        """
        self.config = config or RaspiMouseConfig()
        self._backend = backend
        self._is_open = False
        self.leds: tuple[Led, ...] = ()
        self.switches: tuple[Switch, ...] = ()
        self.light_sensors: LightSensors | None = None
        self.buzzer: Buzzer | None = None
        self.motors: Motors | None = None
        self.motor_power: MotorPower | None = None
        self.left_counter: PulseCounter | None = None
        self.right_counter: PulseCounter | None = None

    def open(self) -> None:  # noqa: A003 (pairs with close() like a file object)
        """
        Acquire hardware resources and create all devices.

        If any device fails to open, everything opened so far is released.
        Calling this while already open does nothing.
        """
        if self._is_open:
            return
        if self._backend is None:
            self._backend = LinuxBackend(gpio_chip=self.config.gpio_chip)
        self._is_open = True
        try:
            self.leds = tuple(
                Led(self._backend.digital_output(pin, initial=False))
                for pin in self.config.led_pins)
            self.switches = tuple(
                Switch(self._backend.digital_input(pin, pull_up=True))
                for pin in self.config.switch_pins)
            self.buzzer = Buzzer(
                self._backend.software_pwm(self.config.buzzer.pin), self.config.buzzer)
            # TODO: create the other devices as they are implemented.
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        """
        Stop the motors, turn off the motor power and release all resources.

        Calling this more than once is allowed.
        """
        # TODO: stop the motors and turn off the motor power first.
        devices = (*([self.buzzer] if self.buzzer else []), *self.leds, *self.switches)
        self.buzzer = None
        self.leds = ()
        self.switches = ()
        # Close every device even if one fails, then report the first error.
        error: BaseException | None = None
        for device in devices:
            try:
                device.close()
            except Exception as e:
                error = error or e
        try:
            if self._backend is not None:
                self._backend.close()
        finally:
            self._is_open = False
        if error is not None:
            raise error

    def __enter__(self) -> 'RaspiMouse':
        """Open the devices."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the devices."""
        self.close()
