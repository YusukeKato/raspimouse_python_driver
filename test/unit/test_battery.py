import pytest

from raspimouse_python_driver.config import BatteryConfig
from raspimouse_python_driver.devices.battery import Battery
from raspimouse_python_driver.devices.mcp3204 import Mcp3204, Mcp3208
from raspimouse_python_driver.hal.mock import mcp3204_responder, MockSpiDevice


def make_battery(raw, config=BatteryConfig()):
    values = {config.adc_channel: raw}
    spi = MockSpiDevice(mcp3204_responder(lambda ch: values.get(ch, 0)))
    return Battery(Mcp3208(spi), config), spi


def test_reads_channel_4():
    battery, spi = make_battery(1234)
    assert battery.read_raw() == 1234
    assert spi.transfers == [b'\x07\x00\x00']


def test_voltage_conversion():
    # 11.1 V -> 11.1 / 6.1 = 1.82 V at the ADC -> 1.82 / 3.3 * 4095 = 2258
    battery, _ = make_battery(2258)
    assert battery.read_voltage() == pytest.approx(11.1, abs=0.01)
    battery, _ = make_battery(0)
    assert battery.read_voltage() == 0


def test_custom_divider():
    config = BatteryConfig(divider_ratio=2.0, reference_voltage=4.095)
    battery, _ = make_battery(1000, config)
    assert battery.read_voltage() == pytest.approx(2.0)


def test_adc_without_the_channel_is_rejected():
    with pytest.raises(ValueError, match='Mcp3204'):
        Battery(Mcp3204(MockSpiDevice()), BatteryConfig())
