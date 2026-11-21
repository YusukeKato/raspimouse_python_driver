import pytest

from raspimouse_python_driver.devices.mcp3204 import Mcp3204, Mcp3208
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


@pytest.mark.parametrize('channel, expected', [
    (4, b'\x07\x00\x00'),
    (5, b'\x07\x40\x00'),
    (7, b'\x07\xc0\x00'),
])
def test_mcp3208_upper_channels_set_d2(channel, expected):
    spi = MockSpiDevice()
    Mcp3208(spi).read(channel)
    assert spi.transfers == [expected]


def test_mcp3208_with_simulator():
    adc = Mcp3208(MockSpiDevice(mcp3204_responder(lambda ch: ch * 100)))
    assert [adc.read(ch) for ch in range(8)] == [0, 100, 200, 300, 400, 500, 600, 700]


@pytest.mark.parametrize('channel', [-1, 8])
def test_mcp3208_invalid_channel(channel):
    with pytest.raises(ValueError):
        Mcp3208(MockSpiDevice()).read(channel)
