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

    def __init__(self, spi: SpiDevice) -> None:
        """Wrap an SPI device."""
        self._spi = spi

    def read(self, channel: int) -> int:
        """Return the conversion result (0-4095) of ``channel`` (0-3)."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the SPI device."""
        raise NotImplementedError
