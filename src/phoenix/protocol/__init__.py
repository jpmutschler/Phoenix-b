"""Protocol definitions and SMBus command encoding."""

from phoenix.protocol.chip_profile import ChipProfile, load_profile
from phoenix.protocol.enums import (
    BifurcationMode,
    MaxDataRate,
    ClockingMode,
    ResetType,
    LTSSMState,
    PRBSPattern,
)
from phoenix.protocol.smbus_commands import SMBusCommand

__all__ = [
    "BifurcationMode",
    "ChipProfile",
    "ClockingMode",
    "LTSSMState",
    "MaxDataRate",
    "PRBSPattern",
    "ResetType",
    "SMBusCommand",
    "load_profile",
]
