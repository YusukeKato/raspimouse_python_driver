"""SPI through lgpio (``/dev/spidevB.C``)."""

from ._lgpio import import_lgpio
from ...exceptions import DeviceError


class LgpioSpiDevice:
    """SPI device (mode 0)."""

    def __init__(self, bus: int, chip_select: int, max_speed_hz: int) -> None:
        """Open ``/dev/spidev{bus}.{chip_select}``."""
        self._lgpio = import_lgpio()
        self.name = f'/dev/spidev{bus}.{chip_select}'
        try:
            self._handle = self._lgpio.spi_open(bus, chip_select, max_speed_hz, 0)
        except self._lgpio.error as e:
            raise DeviceError(f'cannot open {self.name}: {e}') from e
        self._closed = False

    def transfer(self, data: bytes) -> bytes:
        """Full duplex transfer. Returns as many bytes as sent."""
        if self._closed:
            raise DeviceError(f'{self.name} is already closed')
        data = bytes(data)
        try:
            count, received = self._lgpio.spi_xfer(self._handle, data)
        except self._lgpio.error as e:
            raise DeviceError(f'SPI transfer on {self.name} failed: {e}') from e
        if count != len(data):
            raise DeviceError(
                f'SPI transfer on {self.name} returned {count} of {len(data)} bytes')
        return bytes(received)

    def close(self) -> None:
        """Close the device. Calling this more than once is allowed."""
        if self._closed:
            return
        self._closed = True
        try:
            self._lgpio.spi_close(self._handle)
        except self._lgpio.error:
            pass
