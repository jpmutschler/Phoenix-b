"""
Configuration management API routes.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from phoenix.api import app as app_module
from phoenix.models.configuration import DeviceConfiguration, ConfigurationUpdate
from phoenix.protocol.enums import (
    BifurcationMode,
    ClockingMode,
    MaxDataRate,
    PortOrientation,
    ResetType,
)

router = APIRouter()


class ConfigurationResponse(BaseModel):
    """Device configuration response."""

    bifurcation_mode: str
    max_data_rate: str
    clocking_mode: str
    port_orientation: str
    global_interrupt_enable: bool
    eq_phase_error_enable: bool
    phy_phase_error_enable: bool
    internal_error_enable: bool


class ConfigurationUpdateRequest(BaseModel):
    """Configuration update request."""

    bifurcation_mode: Optional[str] = Field(default=None, description="Bifurcation mode")
    max_data_rate: Optional[str] = Field(default=None, description="Maximum data rate")
    clocking_mode: Optional[str] = Field(default=None, description="Clocking mode")
    port_orientation: Optional[str] = Field(default=None, description="Port orientation")


class ResetRequest(BaseModel):
    """Reset request."""

    reset_type: str = Field(
        default="SOFT", description="Reset type: HARD, SOFT, MAC, PERST, GLOBAL_SWRST"
    )


class RegisterAccessRequest(BaseModel):
    """Direct register access request."""

    address: int = Field(description="Register address")
    value: Optional[int] = Field(default=None, description="Value to write (for write operations)")
    width: int = Field(default=32, description="Register width (16 or 32)")


class RegisterResponse(BaseModel):
    """Register read response."""

    address: str
    value: str
    width: int


@router.get("/{handle}/config", response_model=ConfigurationResponse)
async def get_configuration(handle: int) -> ConfigurationResponse:
    """Get current device configuration."""
    try:
        device = app_module.get_device(handle)
        config = await device.get_configuration()
        return ConfigurationResponse(
            bifurcation_mode=config.bifurcation_mode.name,
            max_data_rate=config.max_data_rate.name,
            clocking_mode=config.clocking_mode.name,
            port_orientation=config.port_orientation.name,
            global_interrupt_enable=config.interrupt_config.global_interrupt_enable,
            eq_phase_error_enable=config.interrupt_config.eq_phase_error_enable,
            phy_phase_error_enable=config.interrupt_config.phy_phase_error_enable,
            internal_error_enable=config.interrupt_config.internal_error_enable,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{handle}/config")
async def update_configuration(handle: int, request: ConfigurationUpdateRequest) -> dict:
    """Update device configuration."""
    try:
        device = app_module.get_device(handle)

        update = ConfigurationUpdate()

        if request.bifurcation_mode:
            try:
                update.bifurcation_mode = BifurcationMode[request.bifurcation_mode]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid bifurcation_mode: {request.bifurcation_mode}",
                )

        if request.max_data_rate:
            try:
                update.max_data_rate = MaxDataRate[request.max_data_rate]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid max_data_rate: {request.max_data_rate}",
                )

        if request.clocking_mode:
            try:
                update.clocking_mode = ClockingMode[request.clocking_mode]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid clocking_mode: {request.clocking_mode}",
                )

        if request.port_orientation:
            try:
                update.port_orientation = PortOrientation[request.port_orientation]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid port_orientation: {request.port_orientation}",
                )

        await device.set_configuration(update)
        return {"status": "updated"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handle}/reset")
async def reset_device(handle: int, request: ResetRequest) -> dict:
    """Reset the device."""
    try:
        device = app_module.get_device(handle)

        try:
            reset_type = ResetType[request.reset_type]
        except KeyError:
            raise HTTPException(
                status_code=400, detail=f"Invalid reset_type: {request.reset_type}"
            )

        await device.reset(reset_type)
        return {"status": "reset", "reset_type": reset_type.name}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/register/{address}", response_model=RegisterResponse)
async def read_register(handle: int, address: int, width: int = 32) -> RegisterResponse:
    """Read a register directly."""
    if width not in [16, 32]:
        raise HTTPException(status_code=400, detail="Width must be 16 or 32")

    try:
        device = app_module.get_device(handle)
        value = await device.read_register(address, width)
        return RegisterResponse(
            address=f"0x{address:04X}",
            value=f"0x{value:0{width // 4}X}",
            width=width,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{handle}/register/{address}")
async def write_register(handle: int, address: int, request: RegisterAccessRequest) -> dict:
    """Write a register directly."""
    if request.value is None:
        raise HTTPException(status_code=400, detail="Value required for write")

    if request.width not in [16, 32]:
        raise HTTPException(status_code=400, detail="Width must be 16 or 32")

    try:
        device = app_module.get_device(handle)
        await device.write_register(address, request.value, request.width)
        return {
            "status": "written",
            "address": f"0x{address:04X}",
            "value": f"0x{request.value:0{request.width // 4}X}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/config/bifurcation-modes")
async def list_bifurcation_modes() -> dict:
    """List available bifurcation modes."""
    return {
        "modes": [
            {"name": mode.name, "value": mode.value}
            for mode in BifurcationMode
        ]
    }


@router.get("/{handle}/config/data-rates")
async def list_data_rates() -> dict:
    """List available data rates."""
    return {
        "rates": [
            {"name": rate.name, "value": rate.value, "speed_gt_s": rate.speed_gt_s}
            for rate in MaxDataRate
            if rate != MaxDataRate.RESERVED
        ]
    }


@router.get("/{handle}/config/clocking-modes")
async def list_clocking_modes() -> dict:
    """List available clocking modes."""
    return {
        "modes": [
            {"name": mode.name, "value": mode.value}
            for mode in ClockingMode
            if "RESERVED" not in mode.name
        ]
    }
