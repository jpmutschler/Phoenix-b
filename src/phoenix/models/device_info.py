"""
Device information models for the Broadcom Vantage retimer.
"""

from pydantic import BaseModel, Field

from phoenix.protocol.enums import MaxDataRate, HandleType


class DeviceInfo(BaseModel):
    """Information about a discovered retimer device."""

    product_handle: int = Field(description="Handle for device operations")
    handle_type: HandleType = Field(
        default=HandleType.RETIMER_I2C, description="Type of handle (I2C, UART, MDIO)"
    )
    pci_device_id: int = Field(default=0x8567, description="PCI Device ID (BCM85667)")
    pci_vendor_id: int = Field(default=0x14E4, description="PCI Vendor ID (Broadcom)")
    revision_id: int = Field(default=0, description="Device revision ID")
    num_lanes: int = Field(default=16, description="Number of lanes supported")
    firmware_version: int = Field(default=0, description="Firmware version")
    device_address: int = Field(default=0x50, description="I2C/SMBus device address")
    max_speed: MaxDataRate = Field(
        default=MaxDataRate.GEN6_64G, description="Maximum supported data rate"
    )

    @property
    def device_id_str(self) -> str:
        """Return device ID as a formatted string."""
        return f"0x{self.pci_device_id:04X}"

    @property
    def vendor_id_str(self) -> str:
        """Return vendor ID as a formatted string."""
        return f"0x{self.pci_vendor_id:04X}"

    @property
    def firmware_version_str(self) -> str:
        """Return firmware version as a formatted string."""
        major = (self.firmware_version >> 8) & 0xFF
        minor = self.firmware_version & 0xFF
        return f"{major}.{minor}"

    model_config = {"frozen": False}


class FirmwareInfo(BaseModel):
    """Firmware information."""

    version: int = Field(description="Firmware version")
    crc: int = Field(default=0, description="Firmware CRC")
    size: int = Field(default=0, description="Firmware size in bytes")
    is_valid: bool = Field(default=False, description="Firmware validity flag")

    @property
    def version_str(self) -> str:
        """Return version as a formatted string."""
        major = (self.version >> 8) & 0xFF
        minor = self.version & 0xFF
        return f"{major}.{minor}"

    model_config = {"frozen": False}
