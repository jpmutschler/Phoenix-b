"""Pydantic data models for Phoenix retimer API."""

from phoenix.models.device_info import DeviceInfo
from phoenix.models.status import RetimerStatus, PortStatus, VoltageInfo
from phoenix.models.configuration import (
    DeviceConfiguration,
    TxCoefficients,
    TxEqualizationParams,
)
from phoenix.models.diagnostics import PRBSResult, EyeDiagramResult

__all__ = [
    "DeviceInfo",
    "RetimerStatus",
    "PortStatus",
    "VoltageInfo",
    "DeviceConfiguration",
    "TxCoefficients",
    "TxEqualizationParams",
    "PRBSResult",
    "EyeDiagramResult",
]
