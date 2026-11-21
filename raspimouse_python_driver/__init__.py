"""
Pure Python device driver for Raspberry Pi Mouse.

This package does not depend on ROS. It can be used from plain Python scripts
or imported from ROS 2 nodes.
"""

from .config import RaspiMouseConfig
from .exceptions import (
    BackendUnavailableError,
    DeviceError,
    RaspiMouseError,
)
from .robot import RaspiMouse

__version__ = '0.0.0'

__all__ = [
    'BackendUnavailableError',
    'DeviceError',
    'RaspiMouse',
    'RaspiMouseConfig',
    'RaspiMouseError',
    '__version__',
]
