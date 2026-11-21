"""Battery voltage monitor."""

from .mcp3204 import Mcp3204
from ..config import BatteryConfig


class Battery:
    """
    Battery voltage read through the A/D converter.

    Strictly, this is the input voltage after the main switch: when the robot
    is powered from an AC adapter, it reads the adapter voltage.
    The A/D converter is shared with the light sensors and is not closed here.
    The accuracy depends on the 3.3 V rail used as the reference voltage.
    """

    def __init__(self, adc: Mcp3204, config: BatteryConfig) -> None:
        """Use ``config.adc_channel`` of ``adc`` (an MCP3208 on V3)."""
        if not 0 <= config.adc_channel < adc.CHANNELS:
            raise ValueError(
                f'{type(adc).__name__} has no channel {config.adc_channel}')
        self._adc = adc
        self._config = config

    def read_raw(self) -> int:
        """Return the A/D converter value (0-4095)."""
        return self._adc.read(self._config.adc_channel)

    def read_voltage(self) -> float:
        """Return the battery voltage [V]."""
        c = self._config
        return self.read_raw() / self._adc.MAX_VALUE * c.reference_voltage * c.divider_ratio
