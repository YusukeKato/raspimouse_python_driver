"""
Fake hardware for unit tests and development on a PC.

Each fake records what was written and returns values set by the test.
"""

from ..exceptions import DeviceError


class MockDigitalOutput:
    """Fake GPIO output that records the written levels."""

    def __init__(self, pin: int, initial: bool = False) -> None:
        """Create the fake with the initial level."""
        self.pin = pin
        self.value = bool(initial)
        self.history: list[bool] = [self.value]
        self.closed = False

    def write(self, value: bool) -> None:
        """Record the level."""
        if self.closed:
            raise DeviceError(f'GPIO{self.pin} is already closed')
        self.value = bool(value)
        self.history.append(self.value)

    def close(self) -> None:
        """Mark as closed."""
        self.closed = True


class MockDigitalInput:
    """Fake GPIO input whose level is set by the test."""

    def read(self) -> bool:
        """Return the level set by the test."""
        raise NotImplementedError

    def close(self) -> None:
        """Mark as closed."""
        raise NotImplementedError


class MockSpiDevice:
    """Fake SPI device that answers with a user supplied function."""

    def transfer(self, data: bytes) -> bytes:
        """Record ``data`` and return the prepared response."""
        raise NotImplementedError

    def close(self) -> None:
        """Mark as closed."""
        raise NotImplementedError


class MockI2cDevice:
    """Fake I2C device backed by a register dictionary."""

    def read_byte_data(self, register: int) -> int:
        """Return the register value."""
        raise NotImplementedError

    def write_byte_data(self, register: int, value: int) -> None:
        """Store the register value."""
        raise NotImplementedError

    def close(self) -> None:
        """Mark as closed."""
        raise NotImplementedError


class MockPwmChannel:
    """Fake PWM channel that records frequency and duty ratio."""

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """Record the output settings."""
        raise NotImplementedError

    def stop(self) -> None:
        """Record that output stopped."""
        raise NotImplementedError

    def close(self) -> None:
        """Mark as closed."""
        raise NotImplementedError


class MockBackend:
    """Backend that creates the fakes above and keeps them for inspection."""

    def __init__(self) -> None:
        """Create the backend."""
        self.outputs: dict[int, MockDigitalOutput] = {}
        self.closed = False

    def digital_output(self, pin: int, initial: bool = False) -> MockDigitalOutput:
        """Create a fake output for ``pin``."""
        if pin in self.outputs and not self.outputs[pin].closed:
            raise DeviceError(f'GPIO{pin} is already in use')
        self.closed = False
        output = MockDigitalOutput(pin, initial)
        self.outputs[pin] = output
        return output

    def digital_input(self, pin: int, pull_up: bool = False) -> MockDigitalInput:
        """Create a fake input for ``pin``."""
        raise NotImplementedError

    def software_pwm(self, pin: int) -> MockPwmChannel:
        """Create a fake PWM output for ``pin``."""
        raise NotImplementedError

    def spi_device(self, bus: int, chip_select: int, max_speed_hz: int) -> MockSpiDevice:
        """Create a fake SPI device."""
        raise NotImplementedError

    def i2c_device(self, bus: int, address: int) -> MockI2cDevice:
        """Create a fake I2C device."""
        raise NotImplementedError

    def pwm_channel(self, chip: int, channel: int) -> MockPwmChannel:
        """Create a fake PWM channel."""
        raise NotImplementedError

    def close(self) -> None:
        """Close all fakes."""
        for output in self.outputs.values():
            output.close()
        self.closed = True
