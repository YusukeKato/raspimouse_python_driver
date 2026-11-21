"""Infrared light sensors (4 channels)."""

from typing import NamedTuple

from .mcp3204 import Mcp3204
from ..config import LightSensorConfig
from ..hal.interfaces import DigitalOutput


class LightSensorValues(NamedTuple):
    """Proximity values of the four sensors. Larger is closer."""

    right_front: int
    right: int
    left: int
    left_front: int


class LightSensors:
    """
    Four light sensors sharing one MCP3204.

    Each channel is measured by subtracting the ADC value with the emitter off
    (ambient light) from the value with the emitter on. Channels are measured
    one at a time so that emitters do not interfere with each other.
    """

    def __init__(self, adc: Mcp3204, emitters: dict[str, DigitalOutput],
                 config: LightSensorConfig) -> None:
        """
        Create the sensors.

        :param adc: the shared ADC.
        :param emitters: emitter LED outputs keyed by
            ``right_front``, ``right``, ``left`` and ``left_front``.
        :param config: ADC channels and timing.
        """
        self._adc = adc
        self._emitters = emitters
        self._config = config

    def read(self) -> LightSensorValues:
        """Measure all four channels."""
        raise NotImplementedError

    def close(self) -> None:
        """Turn off all emitters and release resources."""
        raise NotImplementedError
