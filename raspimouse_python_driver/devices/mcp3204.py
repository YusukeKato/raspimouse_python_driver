"""MCP3204 12 bit A/D converter on SPI."""

from ..hal.interfaces import SpiDevice


class Mcp3204:
    """
    MCP3204 in single-ended mode.

    One conversion is a 3 byte transfer: start bit and single-ended bit in the
    first byte, channel number in the top 2 bits of the second byte. The result
    is the low 4 bits of the second response byte and the third response byte.
    """

    CHANNELS = 4
    MAX_VALUE = 4095

    _START = 0x04
    _SINGLE_ENDED = 0x02

    def __init__(self, spi: SpiDevice) -> None:
        """Wrap an SPI device."""
        self._spi = spi

    @classmethod
    def command(cls, channel: int) -> bytes:
        """Return the 3 byte command that converts ``channel``."""
        return bytes([cls._START | cls._SINGLE_ENDED | (channel >> 2),
                      (channel & 0x03) << 6,
                      0x00])

    def read(self, channel: int) -> int:
        """
        Return the conversion result (0-4095) of ``channel`` (0-3).

        :raises ValueError: ``channel`` is out of range.
        """
        if not 0 <= channel < self.CHANNELS:
            raise ValueError(f'channel must be 0-{self.CHANNELS - 1}: {channel}')
        response = self._spi.transfer(self.command(channel))
        return ((response[1] & 0x0F) << 8) | response[2]

    def close(self) -> None:
        """Close the SPI device."""
        self._spi.close()
