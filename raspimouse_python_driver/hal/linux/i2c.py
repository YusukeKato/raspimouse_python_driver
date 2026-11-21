"""I2C through lgpio (``/dev/i2c-N``)."""


class LgpioI2cDevice:
    """I2C device at a fixed address."""

    def __init__(self, bus: int, address: int) -> None:
        """Open ``/dev/i2c-{bus}`` for the device at ``address``."""
        raise NotImplementedError

    def read_byte_data(self, register: int) -> int:
        """Read one byte from a register."""
        raise NotImplementedError

    def write_byte_data(self, register: int, value: int) -> None:
        """Write one byte to a register."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the device."""
        raise NotImplementedError
