import pytest

from raspimouse_python_driver.config import LightSensorConfig
from raspimouse_python_driver.devices.light_sensor import LightSensors, READ_ORDER
from raspimouse_python_driver.devices.mcp3204 import Mcp3204
from raspimouse_python_driver.exceptions import DeviceError
from raspimouse_python_driver.hal.mock import (
    mcp3204_responder,
    MockDigitalOutput,
    MockSpiDevice,
)

CONFIG = LightSensorConfig(settle_time_s=0)
AMBIENT = {'right_front': 100, 'right': 200, 'left': 300, 'left_front': 400}
REFLECTED = {'right_front': 1000, 'right': 20, 'left': 3, 'left_front': 0}


def make_sensors(reflected=None):
    reflected = REFLECTED if reflected is None else reflected
    emitters = {name: MockDigitalOutput(getattr(CONFIG, name).emitter_pin)
                for name in READ_ORDER}
    by_channel = {getattr(CONFIG, name).adc_channel: name for name in READ_ORDER}
    log = []

    def read_channel(channel):
        name = by_channel[channel]
        lit = [n for n, e in emitters.items() if e.value]
        log.append((name, tuple(lit)))
        return AMBIENT[name] + (reflected[name] if name in lit else 0)

    spi = MockSpiDevice(mcp3204_responder(read_channel))
    return LightSensors(Mcp3204(spi), emitters, CONFIG), emitters, spi, log


def test_values_are_lit_minus_ambient():
    sensors, _, _, _ = make_sensors()
    values = sensors.read()
    assert values._asdict() == REFLECTED


def test_value_can_be_negative():
    sensors, _, _, _ = make_sensors(reflected={**REFLECTED, 'left': -5})
    assert sensors.read().left == -5


def test_reads_each_channel_off_then_on_one_emitter_at_a_time():
    sensors, emitters, _, log = make_sensors()
    sensors.read()
    expected = []
    for name in READ_ORDER:
        expected += [(name, ()), (name, (name,))]
    assert log == expected
    assert not any(e.value for e in emitters.values())


def test_emitter_is_turned_off_when_adc_fails():
    sensors, emitters, spi, _ = make_sensors()

    def broken(data):
        if emitters['right'].value:
            raise DeviceError('SPI failed')
        return bytes(3)
    spi.responder = broken
    with pytest.raises(DeviceError):
        sensors.read()
    assert not emitters['right'].value


def test_close_releases_everything():
    sensors, emitters, spi, _ = make_sensors()
    sensors.close()
    assert all(e.closed and not e.value for e in emitters.values())
    assert spi.closed
    sensors.close()  # second close is allowed
    with pytest.raises(DeviceError):
        sensors.read()


def test_missing_emitter_is_rejected():
    _, emitters, spi, _ = make_sensors()
    del emitters['left']
    with pytest.raises(ValueError):
        LightSensors(Mcp3204(spi), emitters, CONFIG)
