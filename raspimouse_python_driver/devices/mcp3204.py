"""MCP3204 / MCP3208 12 bit A/D converters on SPI."""

import threading

from ..hal.interfaces import SpiDevice


class Mcp3204:
    """
    MCP3204 (4 channels) in single-ended mode.

    One conversion is a 3 byte transfer: start bit, single-ended bit and
    channel bit D2 in the first byte, channel bits D1 D0 in the top 2 bits of
    the second byte. The result is the low 4 bits of the second response byte
    and the third response byte. Thread safe.
    """

    CHANNELS = 4
    MAX_VALUE = 4095

    _START = 0x04
    _SINGLE_ENDED = 0x02

    def __init__(self, spi: SpiDevice) -> None:
        """Wrap an SPI device."""
        self._spi = spi
        self._lock = threading.Lock()

    @classmethod
    def command(cls, channel: int) -> bytes:
        """Return the 3 byte command that converts ``channel``."""
        return bytes([cls._START | cls._SINGLE_ENDED | (channel >> 2),
                      (channel & 0x03) << 6,
                      0x00])

    def read(self, channel: int) -> int:
        """
        Return the conversion result (0-4095) of ``channel``.

        :raises ValueError: ``channel`` is out of range.
        """
        if not 0 <= channel < self.CHANNELS:
            raise ValueError(f'channel must be 0-{self.CHANNELS - 1}: {channel}')
        with self._lock:
            response = self._spi.transfer(self.command(channel))
        return ((response[1] & 0x0F) << 8) | response[2]

    def close(self) -> None:
        """Close the SPI device."""
        self._spi.close()


class Mcp3208(Mcp3204):
    """
    MCP3208 (8 channels), the A/D converter of Raspberry Pi Mouse V3.

    Same protocol as the MCP3204; channels 4-7 set bit D2.
    """

    CHANNELS = 8
