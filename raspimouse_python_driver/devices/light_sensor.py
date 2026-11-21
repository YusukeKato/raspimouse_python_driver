"""Infrared light sensors (4 channels)."""

import threading
import time
from typing import NamedTuple

from .mcp3204 import Mcp3204
from ..config import LightSensorConfig
from ..exceptions import DeviceError
from ..hal.interfaces import DigitalOutput

# Same order as the rtmouse kernel driver.
READ_ORDER = ('right', 'left', 'right_front', 'left_front')


class LightSensorValues(NamedTuple):
    """
    Proximity values of the four sensors. Larger is closer.

    Each value is (ADC with emitter on) - (ADC with emitter off), so it can be
    slightly negative when nothing is in front of the sensor.
    """

    right_front: int
    right: int
    left: int
    left_front: int


def _busy_wait(seconds: float) -> None:
    """Wait for a few microseconds. time.sleep() is too coarse for this."""
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        pass


class LightSensors:
    """
    Four light sensors sharing one MCP3204.

    Each channel is measured by subtracting the ADC value with the emitter off
    (ambient light) from the value with the emitter on. Channels are measured
    one at a time so that emitters do not interfere with each other.
    :meth:`read` is thread safe.
    """

    def __init__(self, adc: Mcp3204, emitters: dict[str, DigitalOutput],
                 config: LightSensorConfig, close_adc: bool = True) -> None:
        """
        Create the sensors.

        :param adc: the ADC.
        :param emitters: emitter LED outputs keyed by
            ``right_front``, ``right``, ``left`` and ``left_front``.
        :param config: ADC channels and timing.
        :param close_adc: close ``adc`` in :meth:`close`. False when the ADC is
            shared with other devices (the battery monitor).
        """
        missing = set(READ_ORDER) - set(emitters)
        if missing:
            raise ValueError(f'missing emitters: {sorted(missing)}')
        self._adc = adc
        self._emitters = emitters
        self._config = config
        self._close_adc = close_adc
        self._lock = threading.Lock()
        self._closed = False

    def read(self) -> LightSensorValues:
        """Measure all four channels."""
        with self._lock:
            if self._closed:
                raise DeviceError('light sensors are already closed')
            settle = self._config.settle_time_s
            values = {}
            for name in READ_ORDER:
                channel = getattr(self._config, name).adc_channel
                emitter = self._emitters[name]
                ambient = self._adc.read(channel)
                emitter.write(True)
                try:
                    _busy_wait(settle)
                    lit = self._adc.read(channel)
                finally:
                    emitter.write(False)
                _busy_wait(settle)
                values[name] = lit - ambient
            return LightSensorValues(**values)

    def close(self) -> None:
        """
        Turn off all emitters and release resources.

        Calling this more than once is allowed.
        """
        with self._lock:
            if self._closed:
                return
            self._closed = True
            error: Exception | None = None
            for emitter in self._emitters.values():
                try:
                    emitter.write(False)
                except Exception as e:
                    error = error or e
                emitter.close()
            if self._close_adc:
                self._adc.close()
            if error is not None:
                raise error
