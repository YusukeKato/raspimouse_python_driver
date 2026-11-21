import pytest

from raspimouse_python_driver.config import PulseCounterConfig
from raspimouse_python_driver.devices.pulse_counter import PulseCounter
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import MockI2cDevice

CONFIG = PulseCounterConfig()


class Counter:
    """A fake counter chip and the motor direction seen by PulseCounter."""

    def __init__(self, raw=0):
        self.i2c = MockI2cDevice(CONFIG.left_address)
        self.forward = True
        self.set_raw(raw)
        self.counter = PulseCounter(self.i2c, CONFIG, lambda: self.forward)

    def set_raw(self, raw):
        self.i2c.registers[CONFIG.msb_register] = raw >> 8
        self.i2c.registers[CONFIG.lsb_register] = raw & 0xFF


def test_read_raw_combines_msb_and_lsb():
    c = Counter(0x1234)
    assert c.counter.read_raw() == 0x1234


def test_reads_lsb_before_msb():
    c = Counter()
    order = []
    original = c.i2c.read_byte_data

    def logging_read(register):
        order.append(register)
        return original(register)
    c.i2c.read_byte_data = logging_read
    c.counter.read_raw()
    assert order == [CONFIG.lsb_register, CONFIG.msb_register]


def test_signed_count_follows_direction():
    c = Counter(1000)
    assert c.counter.read_signed() == 0  # starts at 0
    c.set_raw(1400)
    assert c.counter.read_signed() == 400
    c.counter.update()   # what the motor does right before reversing
    c.forward = False
    c.set_raw(1700)
    assert c.counter.read_signed() == 100


def test_wrap_around():
    c = Counter(0xFFF0)
    c.set_raw(0x0005)
    assert c.counter.read_signed() == 0x15  # 16 pulses up to 0xFFFF, then 6 more


def test_reset():
    c = Counter(500)
    c.set_raw(900)
    c.counter.reset(42)
    assert c.counter.read_signed() == 42
    c.set_raw(910)
    assert c.counter.read_signed() == 52


def test_missing_device_fails_on_create():
    i2c = MockI2cDevice(CONFIG.left_address)
    i2c.present = False
    with pytest.raises(DeviceError):
        PulseCounter(i2c, CONFIG, lambda: True)


def test_close():
    c = Counter()
    c.counter.close()
    assert c.i2c.closed
    c.counter.close()  # second close is allowed
    with pytest.raises(DeviceError):
        c.counter.read_signed()
