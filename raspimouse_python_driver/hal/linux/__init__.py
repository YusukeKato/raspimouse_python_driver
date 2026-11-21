"""
Backend for Raspberry Pi 4 on Linux.

* GPIO, SPI, I2C and software PWM: lgpio (apt: ``python3-lgpio``)
* Hardware PWM: ``/sys/class/pwm`` (sysfs, no extra package)

lgpio is imported lazily so that this package can be imported on machines
where it is not installed.
"""

from .gpio import LgpioDigitalInput, LgpioDigitalOutput, LgpioSoftwarePwm
from .i2c import LgpioI2cDevice
from .pwm import SysfsPwmChannel
from .spi import LgpioSpiDevice


class LinuxBackend:
    """:class:`~raspimouse_python_driver.hal.interfaces.Backend` for Raspberry Pi 4."""

    def __init__(self, gpio_chip: int = 0) -> None:
        """Create the backend. Resources are acquired on demand."""
        self.gpio_chip = gpio_chip

    def digital_output(self, pin: int, initial: bool = False) -> LgpioDigitalOutput:
        """Claim a GPIO line as output."""
        raise NotImplementedError

    def digital_input(self, pin: int, pull_up: bool = False) -> LgpioDigitalInput:
        """Claim a GPIO line as input."""
        raise NotImplementedError

    def software_pwm(self, pin: int) -> LgpioSoftwarePwm:
        """Claim a GPIO line for software PWM."""
        raise NotImplementedError

    def spi_device(self, bus: int, chip_select: int, max_speed_hz: int) -> LgpioSpiDevice:
        """Open an SPI device."""
        raise NotImplementedError

    def i2c_device(self, bus: int, address: int) -> LgpioI2cDevice:
        """Open an I2C device."""
        raise NotImplementedError

    def pwm_channel(self, chip: int, channel: int) -> SysfsPwmChannel:
        """Open a hardware PWM channel."""
        raise NotImplementedError

    def close(self) -> None:
        """Release everything acquired through this backend."""
        raise NotImplementedError


__all__ = [
    'LgpioDigitalInput',
    'LgpioDigitalOutput',
    'LgpioI2cDevice',
    'LgpioSoftwarePwm',
    'LgpioSpiDevice',
    'LinuxBackend',
    'SysfsPwmChannel',
]
