"""High level interface that bundles all devices of Raspberry Pi Mouse."""

from .config import RaspiMouseConfig
from .devices.buzzer import Buzzer
from .devices.led import Led
from .devices.light_sensor import LightSensors, READ_ORDER
from .devices.mcp3204 import Mcp3204
from .devices.motor import MotorPower, Motors, StepperMotor
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
            # Motor power first, so that the motor drivers are off as early as possible.
            self.motor_power = MotorPower(
                self._backend.digital_output(self.config.motors.enable_pin, initial=False))
            self.motors = self._open_motors()
            self.leds = tuple(
                Led(self._backend.digital_output(pin, initial=False))
                for pin in self.config.led_pins)
            self.switches = tuple(
                Switch(self._backend.digital_input(pin, pull_up=True))
                for pin in self.config.switch_pins)
            self.buzzer = Buzzer(
                self._backend.software_pwm(self.config.buzzer.pin), self.config.buzzer)
            self.light_sensors = self._open_light_sensors()
            # TODO: create the other devices as they are implemented.
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        """
        Stop the motors, turn off the motor power and release all resources.

        Calling this more than once is allowed.
        """
        # Stop the motors and cut their power first.
        devices = (*([self.motors] if self.motors else []),
                   *([self.motor_power] if self.motor_power else []),
                   *([self.buzzer] if self.buzzer else []),
                   *([self.light_sensors] if self.light_sensors else []),
                   *self.leds, *self.switches)
        self.motors = None
        self.motor_power = None
        self.buzzer = None
        self.light_sensors = None
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

    def _open_motors(self) -> Motors:
        config = self.config.motors
        motors = []
        try:
            for channel in (config.left, config.right):
                direction = self._backend.digital_output(
                    channel.direction_pin, initial=channel.forward_level)
                # The hardware PWM is not freed with the backend, so close it on failure.
                pwm = self._backend.pwm_channel(config.pwm_chip, channel.pwm_channel)
                motors.append(StepperMotor(pwm, direction, channel, config))
        except BaseException:
            for motor in motors:
                motor.close()
            raise
        return Motors(*motors)

    def _open_light_sensors(self) -> LightSensors:
        config = self.config.light_sensors
        # Emitters first: GPIO lines are freed with the backend if SPI fails to open.
        emitters = {
            name: self._backend.digital_output(getattr(config, name).emitter_pin, initial=False)
            for name in READ_ORDER}
        spi = self._backend.spi_device(
            config.spi_bus, config.spi_chip_select, config.spi_max_speed_hz)
        return LightSensors(Mcp3204(spi), emitters, config)

    def __enter__(self) -> 'RaspiMouse':
        """Open the devices."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the devices."""
        self.close()
