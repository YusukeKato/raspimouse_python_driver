"""Shared fixtures for unit tests."""

import sys
import types

import pytest

CHIP_HANDLE = 7
SPI_HANDLE = 3
I2C_HANDLE_BASE = 100


class FakeLgpioError(Exception):
    pass


class FakeLgpio(types.ModuleType):
    """Implements the part of the lgpio API used by the backend."""

    error = FakeLgpioError
    chip_handle = CHIP_HANDLE
    spi_handle = SPI_HANDLE
    SET_PULL_UP = 32

    def __init__(self):
        super().__init__('lgpio')
        self.calls = []
        self.busy_pins = set()
        # Levels returned by gpio_read(); unknown pins read high (pulled up).
        self.levels = {}
        # GPIOs with running software PWM.
        self.pwm_active = set()
        # Answers SPI transfers; default: zeros.
        self.spi_responder = lambda data: bytes(len(data))
        self.spi_fail = False
        # I2C registers by device address; addresses in i2c_missing do not answer.
        self.i2c_registers = {0x10: {}, 0x11: {}}
        self.i2c_missing = set()

    def gpiochip_open(self, gpiochip):
        self.calls.append(('gpiochip_open', gpiochip))
        return CHIP_HANDLE

    def gpiochip_close(self, handle):
        self.calls.append(('gpiochip_close', handle))
        return 0

    def gpio_claim_output(self, handle, gpio, level=0, lFlags=0):
        if gpio in self.busy_pins:
            raise FakeLgpioError("'GPIO busy'")
        self.calls.append(('gpio_claim_output', handle, gpio, level))
        return 0

    def gpio_claim_input(self, handle, gpio, lFlags=0):
        if gpio in self.busy_pins:
            raise FakeLgpioError("'GPIO busy'")
        self.calls.append(('gpio_claim_input', handle, gpio, lFlags))
        return 0

    def gpio_read(self, handle, gpio):
        return self.levels.get(gpio, 1)

    def tx_pwm(self, handle, gpio, pwm_frequency, pwm_duty_cycle,
               pulse_offset=0, pulse_cycles=0):
        # Like lgpio 0.2: "off" for a GPIO without active PWM is an error.
        if pwm_frequency == 0 and gpio not in self.pwm_active:
            raise FakeLgpioError("'bad PWM micros'")
        self.calls.append(('tx_pwm', handle, gpio, pwm_frequency, pwm_duty_cycle))
        if pwm_frequency == 0:
            self.pwm_active.discard(gpio)
        else:
            self.pwm_active.add(gpio)
        return 0

    def spi_open(self, spi_device, spi_channel, baud, spi_flags=0):
        if self.spi_fail:
            raise FakeLgpioError("'can not open SPI device'")
        self.calls.append(('spi_open', spi_device, spi_channel, baud, spi_flags))
        return SPI_HANDLE

    def spi_xfer(self, handle, data):
        self.calls.append(('spi_xfer', handle, bytes(data)))
        return [len(data), bytearray(self.spi_responder(bytes(data)))]

    def spi_close(self, handle):
        self.calls.append(('spi_close', handle))
        return 0

    def i2c_open(self, i2c_bus, i2c_address, i2c_flags=0):
        self.calls.append(('i2c_open', i2c_bus, i2c_address))
        return I2C_HANDLE_BASE + i2c_address

    def i2c_read_byte_data(self, handle, reg):
        address = handle - I2C_HANDLE_BASE
        if address in self.i2c_missing:
            raise FakeLgpioError("'I2C read failed'")
        return self.i2c_registers.setdefault(address, {}).get(reg, 0)

    def i2c_write_byte_data(self, handle, reg, byte_val):
        address = handle - I2C_HANDLE_BASE
        self.i2c_registers.setdefault(address, {})[reg] = byte_val
        return 0

    def i2c_close(self, handle):
        self.calls.append(('i2c_close', handle - I2C_HANDLE_BASE))
        return 0

    def set_count(self, address, value):
        """Set the raw 16 bit count of the counter at ``address``."""
        self.i2c_registers[address] = {0x10: value >> 8, 0x11: value & 0xFF}

    def gpio_write(self, handle, gpio, level):
        self.calls.append(('gpio_write', handle, gpio, level))
        return 0

    def last_write(self, gpio):
        writes = [c for c in self.calls if c[0] == 'gpio_write' and c[2] == gpio]
        return writes[-1] if writes else None

    def gpio_free(self, handle, gpio):
        self.calls.append(('gpio_free', handle, gpio))
        return 0


def make_sysfs_pwm(root, chip=0, channels=2, exported=True):
    """Create a fake /sys/class/pwm with pwmchip{chip} and its channels."""
    chip_dir = root / f'pwmchip{chip}'
    chip_dir.mkdir(parents=True)
    for name in ('export', 'unexport'):
        (chip_dir / name).write_text('')
    (chip_dir / 'npwm').write_text(f'{channels}\n')
    if exported:
        for channel in range(channels):
            pwm = chip_dir / f'pwm{channel}'
            pwm.mkdir()
            for name in ('period', 'duty_cycle', 'enable'):
                (pwm / name).write_text('0\n')
    return chip_dir


@pytest.fixture(name='make_sysfs_pwm')
def make_sysfs_pwm_fixture():
    """Return :func:`make_sysfs_pwm` for tests that build their own tree."""
    return make_sysfs_pwm


@pytest.fixture
def sysfs_pwm(tmp_path, monkeypatch):
    """Point the sysfs PWM backend at a fake tree; return pwmchip0."""
    root = tmp_path / 'pwm'
    chip_dir = make_sysfs_pwm(root)
    monkeypatch.setattr('raspimouse_python_driver.hal.linux.pwm.SYSFS_PWM_ROOT', root)
    return chip_dir


@pytest.fixture
def lgpio(monkeypatch, sysfs_pwm):
    fake = FakeLgpio()
    monkeypatch.setitem(sys.modules, 'lgpio', fake)
    return fake
