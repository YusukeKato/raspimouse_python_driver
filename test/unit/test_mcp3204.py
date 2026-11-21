import pytest

from raspimouse_python_driver.devices.mcp3204 import Mcp3204
from raspimouse_python_driver.hal.mock import mcp3204_responder, MockSpiDevice


@pytest.mark.parametrize('channel, expected', [
    (0, b'\x06\x00\x00'),
    (1, b'\x06\x40\x00'),
    (2, b'\x06\x80\x00'),
    (3, b'\x06\xc0\x00'),
])
def test_command_bytes(channel, expected):
    spi = MockSpiDevice()
    Mcp3204(spi).read(channel)
    assert spi.transfers == [expected]


def test_decodes_12_bit_result():
    # Upper nibble of the second byte must be ignored.
    spi = MockSpiDevice(lambda data: bytes([0xFF, 0xFA, 0xBC]))
    assert Mcp3204(spi).read(0) == 0xABC


def test_with_simulator():
    values = {0: 0, 1: 1, 2: 2048, 3: 4095}
    adc = Mcp3204(MockSpiDevice(mcp3204_responder(values.__getitem__)))
    assert [adc.read(ch) for ch in range(4)] == [0, 1, 2048, 4095]


@pytest.mark.parametrize('channel', [-1, 4])
def test_invalid_channel(channel):
    spi = MockSpiDevice()
    with pytest.raises(ValueError):
        Mcp3204(spi).read(channel)
    assert spi.transfers == []


def test_close_closes_spi():
    spi = MockSpiDevice()
    Mcp3204(spi).close()
    assert spi.closed
