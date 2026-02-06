"""
Phoenix - Python API for Broadcom Vantage PCIe Gen6 Retimer chips.

This package provides a comprehensive API for controlling and monitoring
BCM85667 PCIe Gen6 retimer devices via I2C/SMBus or UART interfaces.
"""

from phoenix.core.device import RetimerDevice
from phoenix.core.discovery import DeviceDiscovery
from phoenix.exceptions import (
    PhoenixError,
    TransportError,
    DeviceNotFoundError,
    InvalidParameterError,
    FirmwareError,
    TimeoutError,
    PECMismatchError,
)

__version__ = "0.1.0"
__all__ = [
    "RetimerDevice",
    "DeviceDiscovery",
    "PhoenixError",
    "TransportError",
    "DeviceNotFoundError",
    "InvalidParameterError",
    "FirmwareError",
    "TimeoutError",
    "PECMismatchError",
    "setup_ui",
]


def setup_ui(app):
    """Lazy import and setup NiceGUI dashboard.

    Args:
        app: FastAPI application instance.
    """
    from phoenix.ui import setup_ui as _setup_ui
    _setup_ui(app)
