"""I2C through lgpio (``/dev/i2c-N``)."""

from ._lgpio import import_lgpio
from ...exceptions import DeviceError


class LgpioI2cDevice:
    """I2C device at a fixed address."""

    def __init__(self, bus: int, address: int) -> None:
        """Open ``/dev/i2c-{bus}`` for the device at ``address``."""
        self._lgpio = import_lgpio()
        self.name = f'I2C device 0x{address:02x} on /dev/i2c-{bus}'
        try:
            self._handle = self._lgpio.i2c_open(bus, address, 0)
        except self._lgpio.error as e:
            raise DeviceError(f'cannot open {self.name}: {e}') from e
        self._closed = False

    def read_byte_data(self, register: int) -> int:
        """Read one byte from a register."""
        self._check_open()
        try:
            return self._lgpio.i2c_read_byte_data(self._handle, register)
        except self._lgpio.error as e:
            raise DeviceError(
                f'cannot read register 0x{register:02x} of {self.name}: {e}') from e

    def write_byte_data(self, register: int, value: int) -> None:
        """Write one byte to a register."""
        self._check_open()
        try:
            self._lgpio.i2c_write_byte_data(self._handle, register, value)
        except self._lgpio.error as e:
            raise DeviceError(
                f'cannot write register 0x{register:02x} of {self.name}: {e}') from e

    def close(self) -> None:
        """Close the device. Calling this more than once is allowed."""
        if self._closed:
            return
        self._closed = True
        try:
            self._lgpio.i2c_close(self._handle)
        except self._lgpio.error:
            pass

    def _check_open(self) -> None:
        if self._closed:
            raise DeviceError(f'{self.name} is already closed')
