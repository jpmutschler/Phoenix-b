"""
Configuration data models for the Broadcom Vantage retimer.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from phoenix.protocol.enums import (
    BifurcationMode,
    ClockingMode,
    MaxDataRate,
    PCIeGeneration,
    PortOrientation,
)


class TxCoefficients(BaseModel):
    """TX equalization coefficients for a lane."""

    tx_preset: int = Field(default=0, ge=0, le=15, description="TX preset (0-15)")
    tx_preset_req: int = Field(
        default=0, ge=0, le=15, description="TX preset request to link partner"
    )
    tx_pre_cursor: int = Field(default=0, ge=0, le=63, description="TX pre-cursor")
    tx_post_cursor: int = Field(default=0, ge=0, le=63, description="TX post-cursor")
    tx_cursor: int = Field(default=0, ge=0, le=63, description="TX cursor")
    tx_precode_req: bool = Field(
        default=False, description="TX precoding request (Gen5+ only)"
    )
    tx_preset_sel: bool = Field(
        default=False, description="Use preset (False) or coefficients (True)"
    )
    tx_pre2_cursor: int = Field(
        default=0, ge=0, le=63, description="TX pre2-cursor (Gen6 only)"
    )

    model_config = {"frozen": False}


class TxEqualizationParams(BaseModel):
    """TX equalization phase 2/3 parameters."""

    generation: PCIeGeneration = Field(description="PCIe generation")
    tx_preset_sel: bool = Field(
        default=False, description="Use preset (False) or coefficients (True)"
    )
    tx_preset: int = Field(default=0, ge=0, le=15, description="TX preset")
    tx_pre_cursor: int = Field(default=0, ge=0, le=63, description="TX pre-cursor")
    tx_post_cursor: int = Field(default=0, ge=0, le=63, description="TX post-cursor")
    tx_pre2_cursor: int = Field(default=0, ge=0, le=63, description="TX pre2-cursor")

    model_config = {"frozen": False}


class LaneConfiguration(BaseModel):
    """Configuration for a single lane."""

    lane_number: int = Field(ge=0, le=15, description="Lane number (0-15)")
    gen3_coefficients: TxCoefficients = Field(
        default_factory=TxCoefficients, description="Gen3 TX coefficients"
    )
    gen4_coefficients: TxCoefficients = Field(
        default_factory=TxCoefficients, description="Gen4 TX coefficients"
    )
    gen5_coefficients: TxCoefficients = Field(
        default_factory=TxCoefficients, description="Gen5 TX coefficients"
    )
    gen6_coefficients: TxCoefficients = Field(
        default_factory=TxCoefficients, description="Gen6 TX coefficients"
    )

    def get_coefficients(self, generation: PCIeGeneration) -> TxCoefficients:
        """Get TX coefficients for a specific generation."""
        gen_map = {
            PCIeGeneration.GEN3: self.gen3_coefficients,
            PCIeGeneration.GEN4: self.gen4_coefficients,
            PCIeGeneration.GEN5: self.gen5_coefficients,
            PCIeGeneration.GEN6: self.gen6_coefficients,
        }
        return gen_map.get(generation, self.gen3_coefficients)

    model_config = {"frozen": False}


class InterruptConfiguration(BaseModel):
    """Interrupt mask configuration."""

    global_interrupt_enable: bool = Field(
        default=False, description="Global interrupt enable"
    )
    eq_phase_error_enable: bool = Field(
        default=False, description="EQ phase error interrupt enable"
    )
    phy_phase_error_enable: bool = Field(
        default=False, description="PHY phase error interrupt enable"
    )
    internal_error_enable: bool = Field(
        default=False, description="Internal error interrupt enable"
    )

    model_config = {"frozen": False}


class DeviceConfiguration(BaseModel):
    """Complete device configuration."""

    bifurcation_mode: BifurcationMode = Field(
        default=BifurcationMode.X16, description="Bifurcation mode"
    )
    max_data_rate: MaxDataRate = Field(
        default=MaxDataRate.GEN6_64G, description="Maximum data rate"
    )
    clocking_mode: ClockingMode = Field(
        default=ClockingMode.COMMON_WO_SSC, description="Clocking mode"
    )
    port_orientation: PortOrientation = Field(
        default=PortOrientation.STATIC, description="Port orientation"
    )
    interrupt_config: InterruptConfiguration = Field(
        default_factory=InterruptConfiguration, description="Interrupt configuration"
    )
    lane_configurations: List[LaneConfiguration] = Field(
        default_factory=list, description="Per-lane configurations"
    )

    model_config = {"frozen": False}


class ConfigurationUpdate(BaseModel):
    """Configuration update request (partial update supported)."""

    bifurcation_mode: Optional[BifurcationMode] = Field(
        default=None, description="Bifurcation mode"
    )
    max_data_rate: Optional[MaxDataRate] = Field(
        default=None, description="Maximum data rate"
    )
    clocking_mode: Optional[ClockingMode] = Field(
        default=None, description="Clocking mode"
    )
    port_orientation: Optional[PortOrientation] = Field(
        default=None, description="Port orientation"
    )

    model_config = {"frozen": False}
