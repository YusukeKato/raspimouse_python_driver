"""Hardware abstraction layer (GPIO, SPI, I2C, PWM)."""

from .interfaces import (
    Backend,
    DigitalInput,
    DigitalOutput,
    I2cDevice,
    PwmChannel,
    SpiDevice,
)

__all__ = [
    'Backend',
    'DigitalInput',
    'DigitalOutput',
    'I2cDevice',
    'PwmChannel',
    'SpiDevice',
]
