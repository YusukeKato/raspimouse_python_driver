"""High level interface that bundles all devices of Raspberry Pi Mouse."""

from .config import RaspiMouseConfig
from .devices.buzzer import Buzzer
from .devices.led import Led
from .devices.light_sensor import LightSensors
from .devices.motor import MotorPower, Motors
from .devices.pulse_counter import PulseCounter
from .devices.switch import Switch
from .hal.interfaces import Backend


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
        self.leds: tuple[Led, ...] = ()
        self.switches: tuple[Switch, ...] = ()
        self.light_sensors: LightSensors | None = None
        self.buzzer: Buzzer | None = None
        self.motors: Motors | None = None
        self.motor_power: MotorPower | None = None
        self.left_counter: PulseCounter | None = None
        self.right_counter: PulseCounter | None = None

    def open(self) -> None:  # noqa: A003 (pairs with close() like a file object)
        """Acquire hardware resources and create all devices."""
        # TODO: create LinuxBackend if no backend is given, then build devices.
        raise NotImplementedError

    def close(self) -> None:
        """Stop the motors, turn off the motor power and release all resources."""
        raise NotImplementedError

    def __enter__(self) -> 'RaspiMouse':
        """Open the devices."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the devices."""
        self.close()
