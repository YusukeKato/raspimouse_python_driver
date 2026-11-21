"""Exceptions raised by raspimouse_python_driver."""


class RaspiMouseError(Exception):
    """Base class of all errors raised by this package."""


class BackendUnavailableError(RaspiMouseError):
    """A hardware backend or its dependency (lgpio) is unavailable."""


class DeviceError(RaspiMouseError):
    """Communication with a device failed (e.g. I2C/SPI transfer error)."""
