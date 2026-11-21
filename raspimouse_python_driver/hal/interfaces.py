"""
Hardware abstraction interfaces.

Devices depend only on these protocols, so they can run on real hardware
(:mod:`.linux`) or on a PC with fake hardware (:mod:`.mock`).
"""

from typing import Protocol


class DigitalOutput(Protocol):
    """A GPIO output line."""

    def write(self, value: bool) -> None:
        """Drive the line high (True) or low (False)."""

    def close(self) -> None:
        """Release the line."""


class DigitalInput(Protocol):
    """A GPIO input line."""

    def read(self) -> bool:
        """Return the current level of the line."""

    def close(self) -> None:
        """Release the line."""


class SpiDevice(Protocol):
    """An SPI device (bus + chip select)."""

    def transfer(self, data: bytes) -> bytes:
        """Full duplex transfer. Returns as many bytes as sent."""

    def close(self) -> None:
        """Close the device."""


class I2cDevice(Protocol):
    """An I2C device at a fixed address."""

    def read_byte_data(self, register: int) -> int:
        """Read one byte from a register."""

    def write_byte_data(self, register: int, value: int) -> None:
        """Write one byte to a register."""

    def close(self) -> None:
        """Close the device."""


class PwmChannel(Protocol):
    """A hardware PWM channel."""

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """Start (or update) output with the given frequency and duty ratio."""

    def stop(self) -> None:
        """Stop output."""

    def close(self) -> None:
        """Stop output and release the channel."""


class Backend(Protocol):
    """Factory of hardware resources."""

    def digital_output(self, pin: int, initial: bool = False) -> DigitalOutput:
        """Request a GPIO line as output."""

    def digital_input(self, pin: int, pull_up: bool = False) -> DigitalInput:
        """Request a GPIO line as input."""

    def software_pwm(self, pin: int) -> PwmChannel:
        """Request a GPIO line driven by software timed PWM."""

    def spi_device(self, bus: int, chip_select: int, max_speed_hz: int) -> SpiDevice:
        """Open an SPI device."""

    def i2c_device(self, bus: int, address: int) -> I2cDevice:
        """Open an I2C device."""

    def pwm_channel(self, chip: int, channel: int) -> PwmChannel:
        """Open a hardware PWM channel."""

    def close(self) -> None:
        """Release everything acquired through this backend."""
