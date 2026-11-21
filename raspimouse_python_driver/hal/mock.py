"""
Fake hardware for unit tests and development on a PC.

Each fake records what was written and returns values set by the test.
"""

from collections.abc import Callable

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
    """
    Fake GPIO input whose level is set by the test.

    The level starts high with pull-up and low without, like an open line.
    """

    def __init__(self, pin: int, pull_up: bool = False) -> None:
        """Create the fake."""
        self.pin = pin
        self.pull_up = pull_up
        self.level = pull_up
        self.closed = False

    def read(self) -> bool:
        """Return the level set by the test."""
        if self.closed:
            raise DeviceError(f'GPIO{self.pin} is already closed')
        return self.level

    def close(self) -> None:
        """Mark as closed."""
        self.closed = True


class MockSpiDevice:
    """
    Fake SPI device that answers with a user supplied function.

    ``responder`` receives the sent bytes and returns the received bytes.
    Without one, the device answers with zeros.
    """

    def __init__(self, responder: Callable[[bytes], bytes] | None = None) -> None:
        """Create the fake."""
        self.responder = responder or (lambda data: bytes(len(data)))
        self.transfers: list[bytes] = []
        self.closed = False

    def transfer(self, data: bytes) -> bytes:
        """Record ``data`` and return the prepared response."""
        if self.closed:
            raise DeviceError('SPI device is already closed')
        data = bytes(data)
        self.transfers.append(data)
        response = bytes(self.responder(data))
        if len(response) != len(data):
            raise ValueError('responder must return as many bytes as sent')
        return response

    def close(self) -> None:
        """Mark as closed."""
        self.closed = True


def mcp3204_responder(read_channel: Callable[[int], int]) -> Callable[[bytes], bytes]:
    """
    Return a :class:`MockSpiDevice` responder that behaves like an MCP3204.

    ``read_channel`` returns the conversion result (0-4095) of a channel.
    """
    def respond(data: bytes) -> bytes:
        channel = ((data[0] & 0x01) << 2) | (data[1] >> 6)
        value = read_channel(channel) & 0x0FFF
        return bytes([0x00, value >> 8, value & 0xFF])
    return respond


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

    def __init__(self) -> None:
        """Create a stopped fake."""
        self.frequency_hz: float = 0
        self.duty_ratio: float = 0
        # (frequency_hz, duty_ratio) for each change; (0, 0) means stopped.
        self.history: list[tuple[float, float]] = []
        self.closed = False

    @property
    def running(self) -> bool:
        """Return True while output is on."""
        return self.frequency_hz > 0

    def set_frequency(self, frequency_hz: float, duty_ratio: float = 0.5) -> None:
        """Record the output settings."""
        self._check_open()
        self.frequency_hz = frequency_hz
        self.duty_ratio = duty_ratio
        self.history.append((frequency_hz, duty_ratio))

    def stop(self) -> None:
        """Record that output stopped."""
        self._check_open()
        self.frequency_hz = 0
        self.duty_ratio = 0
        self.history.append((0, 0))

    def close(self) -> None:
        """Mark as closed."""
        self.closed = True

    def _check_open(self) -> None:
        if self.closed:
            raise DeviceError('PWM channel is already closed')


class MockBackend:
    """Backend that creates the fakes above and keeps them for inspection."""

    def __init__(self) -> None:
        """Create the backend."""
        self.outputs: dict[int, MockDigitalOutput] = {}
        self.inputs: dict[int, MockDigitalInput] = {}
        self.software_pwms: dict[int, MockPwmChannel] = {}
        # Keyed by (bus, chip_select). New devices answer with spi_responder.
        self.spi_devices: dict[tuple[int, int], MockSpiDevice] = {}
        self.spi_responder: Callable[[bytes], bytes] | None = None
        self.closed = False

    def _claim(self, pin: int) -> None:
        for lines in (self.outputs, self.inputs, self.software_pwms):
            if pin in lines and not lines[pin].closed:
                raise DeviceError(f'GPIO{pin} is already in use')
        self.closed = False

    def digital_output(self, pin: int, initial: bool = False) -> MockDigitalOutput:
        """Create a fake output for ``pin``."""
        self._claim(pin)
        output = MockDigitalOutput(pin, initial)
        self.outputs[pin] = output
        return output

    def digital_input(self, pin: int, pull_up: bool = False) -> MockDigitalInput:
        """Create a fake input for ``pin``."""
        self._claim(pin)
        line = MockDigitalInput(pin, pull_up)
        self.inputs[pin] = line
        return line

    def software_pwm(self, pin: int) -> MockPwmChannel:
        """Create a fake PWM output for ``pin``."""
        self._claim(pin)
        pwm = MockPwmChannel()
        self.software_pwms[pin] = pwm
        return pwm

    def spi_device(self, bus: int, chip_select: int, max_speed_hz: int) -> MockSpiDevice:
        """Create a fake SPI device. Like the real backend, close() does not close it."""
        key = (bus, chip_select)
        if key in self.spi_devices and not self.spi_devices[key].closed:
            raise DeviceError(f'/dev/spidev{bus}.{chip_select} is already in use')
        device = MockSpiDevice(self.spi_responder)
        self.spi_devices[key] = device
        return device

    def i2c_device(self, bus: int, address: int) -> MockI2cDevice:
        """Create a fake I2C device."""
        raise NotImplementedError

    def pwm_channel(self, chip: int, channel: int) -> MockPwmChannel:
        """Create a fake PWM channel."""
        raise NotImplementedError

    def close(self) -> None:
        """Close all fakes."""
        for line in (*self.outputs.values(), *self.inputs.values(),
                     *self.software_pwms.values()):
            line.close()
        self.closed = True
