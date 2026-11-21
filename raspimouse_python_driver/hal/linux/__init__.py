"""
Backend for Raspberry Pi 4 on Linux.

* GPIO, SPI, I2C and software PWM: lgpio (apt: ``python3-lgpio``)
* Hardware PWM: ``/sys/class/pwm`` (sysfs, no extra package)

lgpio is imported lazily so that this package can be imported on machines
where it is not installed.
"""

from ._lgpio import import_lgpio
from .gpio import LgpioDigitalInput, LgpioDigitalOutput, LgpioSoftwarePwm
from .i2c import LgpioI2cDevice
from .pwm import SysfsPwmChannel
from .spi import LgpioSpiDevice
from ...exceptions import DeviceError


class LinuxBackend:
    """:class:`~raspimouse_python_driver.hal.interfaces.Backend` for Raspberry Pi 4."""

    def __init__(self, gpio_chip: int = 0) -> None:
        """Create the backend. Resources are acquired on demand."""
        self.gpio_chip = gpio_chip
        self._chip_handle: int | None = None

    def _get_chip_handle(self) -> int:
        """Open the GPIO chip on first use and return its handle."""
        if self._chip_handle is None:
            lgpio = import_lgpio()
            try:
                self._chip_handle = lgpio.gpiochip_open(self.gpio_chip)
            except lgpio.error as e:
                raise DeviceError(
                    f'cannot open /dev/gpiochip{self.gpio_chip}: {e}') from e
        return self._chip_handle

    def digital_output(self, pin: int, initial: bool = False) -> LgpioDigitalOutput:
        """Claim a GPIO line as output."""
        return LgpioDigitalOutput(self._get_chip_handle(), pin, initial)

    def digital_input(self, pin: int, pull_up: bool = False) -> LgpioDigitalInput:
        """Claim a GPIO line as input."""
        return LgpioDigitalInput(self._get_chip_handle(), pin, pull_up)

    def software_pwm(self, pin: int) -> LgpioSoftwarePwm:
        """Claim a GPIO line for software PWM."""
        return LgpioSoftwarePwm(self._get_chip_handle(), pin)

    def spi_device(self, bus: int, chip_select: int, max_speed_hz: int) -> LgpioSpiDevice:
        """Open an SPI device. The caller closes it."""
        return LgpioSpiDevice(bus, chip_select, max_speed_hz)

    def i2c_device(self, bus: int, address: int) -> LgpioI2cDevice:
        """Open an I2C device."""
        raise NotImplementedError

    def pwm_channel(self, chip: int, channel: int) -> SysfsPwmChannel:
        """Open a hardware PWM channel. The caller closes it."""
        return SysfsPwmChannel(chip, channel)

    def close(self) -> None:
        """
        Close the GPIO chip, which also frees all lines claimed on it.

        The backend can be used again after this; the chip is reopened on demand.
        """
        if self._chip_handle is None:
            return
        lgpio = import_lgpio()
        handle, self._chip_handle = self._chip_handle, None
        try:
            lgpio.gpiochip_close(handle)
        except lgpio.error as e:
            raise DeviceError(f'cannot close /dev/gpiochip{self.gpio_chip}: {e}') from e


__all__ = [
    'LgpioDigitalInput',
    'LgpioDigitalOutput',
    'LgpioI2cDevice',
    'LgpioSoftwarePwm',
    'LgpioSpiDevice',
    'LinuxBackend',
    'SysfsPwmChannel',
]
