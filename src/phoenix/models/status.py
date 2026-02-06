"""
Status data models for the Broadcom Vantage retimer.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from phoenix.protocol.enums import (
    ForwardingMode,
    LTSSMState,
    MaxDataRate,
    PortType,
    LinkState,
)


class VoltageInfo(BaseModel):
    """Voltage levels from the retimer."""

    dvdd1_mv: int = Field(default=0, description="DVDD1 voltage in millivolts")
    dvdd2_mv: int = Field(default=0, description="DVDD2 voltage in millivolts")
    dvdd3_mv: int = Field(default=0, description="DVDD3 voltage in millivolts")
    dvdd4_mv: int = Field(default=0, description="DVDD4 voltage in millivolts")
    dvdd5_mv: int = Field(default=0, description="DVDD5 voltage in millivolts")
    dvdd6_mv: int = Field(default=0, description="DVDD6 voltage in millivolts")
    dvddio_mv: int = Field(default=0, description="DVDDIO voltage in millivolts")

    model_config = {"frozen": False}


class LaneStatus(BaseModel):
    """Status for a single lane."""

    lane_number: int = Field(description="Lane number (0-15)")
    rx_detect: bool = Field(default=False, description="Receiver detected")
    tx_eq_done: bool = Field(default=False, description="TX equalization complete")
    rx_eq_done: bool = Field(default=False, description="RX equalization complete")

    model_config = {"frozen": False}


class PortStatus(BaseModel):
    """Status for a pseudo port (PPA or PPB)."""

    port_number: int = Field(description="Port number (0-7)")
    port_type: PortType = Field(
        default=PortType.UNKNOWN, description="Port type (upstream/downstream)"
    )
    forwarding_mode: ForwardingMode = Field(
        default=ForwardingMode.DISABLED, description="Forwarding mode status"
    )
    current_ltssm_state: LTSSMState = Field(
        default=LTSSMState.DETECT, description="Current LTSSM state"
    )
    current_link_speed: MaxDataRate = Field(
        default=MaxDataRate.RESERVED, description="Current link speed"
    )
    current_link_width: int = Field(default=0, description="Current link width")
    link_state: LinkState = Field(default=LinkState.DOWN, description="Link state")
    enabled_lanes: int = Field(default=0, description="Number of enabled lanes")
    lane_status: List[LaneStatus] = Field(
        default_factory=list, description="Per-lane status"
    )

    @property
    def is_link_up(self) -> bool:
        """Check if link is up."""
        return self.link_state == LinkState.UP

    @property
    def is_forwarding(self) -> bool:
        """Check if forwarding is enabled."""
        return self.forwarding_mode == ForwardingMode.ENABLED

    model_config = {"frozen": False}


class InterruptStatus(BaseModel):
    """Interrupt status information."""

    global_interrupt: bool = Field(default=False, description="Global interrupt status")
    eq_phase_error: bool = Field(
        default=False, description="Equalization phase error"
    )
    phy_phase_error: bool = Field(default=False, description="PHY phase error")
    internal_error: bool = Field(default=False, description="Internal error")

    model_config = {"frozen": False}


class ErrorStatistics(BaseModel):
    """Error statistics for a lane."""

    lane_number: int = Field(description="Lane number")
    invalid_symbol: int = Field(default=0, description="Invalid symbol count")
    symbol_lock_loss: int = Field(default=0, description="Symbol lock loss count")
    elastic_buffer_error: int = Field(default=0, description="Elastic buffer error count")
    lane_deskew_error: int = Field(default=0, description="Lane deskew error count")
    block_alignment_loss: int = Field(default=0, description="Block alignment loss count")
    block_header_error: int = Field(default=0, description="Block header error count")
    sos_block_error: int = Field(default=0, description="SOS block error count")

    @property
    def total_errors(self) -> int:
        """Return total error count."""
        return (
            self.invalid_symbol
            + self.symbol_lock_loss
            + self.elastic_buffer_error
            + self.lane_deskew_error
            + self.block_alignment_loss
            + self.block_header_error
            + self.sos_block_error
        )

    model_config = {"frozen": False}


class RetimerStatus(BaseModel):
    """Complete status of the retimer device."""

    temperature_c: int = Field(default=0, description="Temperature in degrees Celsius")
    voltage_info: VoltageInfo = Field(
        default_factory=VoltageInfo, description="Voltage levels"
    )
    ppa_status: PortStatus = Field(
        default_factory=lambda: PortStatus(port_number=0),
        description="Pseudo Port A status",
    )
    ppb_status: PortStatus = Field(
        default_factory=lambda: PortStatus(port_number=1),
        description="Pseudo Port B status",
    )
    interrupt_status: InterruptStatus = Field(
        default_factory=InterruptStatus, description="Interrupt status"
    )
    error_statistics: List[ErrorStatistics] = Field(
        default_factory=list, description="Per-lane error statistics"
    )
    firmware_version: int = Field(default=0, description="Firmware version")

    @property
    def is_healthy(self) -> bool:
        """Check if device appears healthy."""
        return (
            not self.interrupt_status.internal_error
            and self.temperature_c < 100  # Temperature threshold
        )

    model_config = {"frozen": False}
