"""SPI through lgpio (``/dev/spidevB.C``)."""


class LgpioSpiDevice:
    """SPI device (mode 0)."""

    def __init__(self, bus: int, chip_select: int, max_speed_hz: int) -> None:
        """Open ``/dev/spidev{bus}.{chip_select}``."""
        raise NotImplementedError

    def transfer(self, data: bytes) -> bytes:
        """Full duplex transfer. Returns as many bytes as sent."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the device."""
        raise NotImplementedError
