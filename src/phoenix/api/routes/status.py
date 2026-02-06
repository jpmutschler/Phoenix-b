"""
Status monitoring API routes.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from phoenix.api import app as app_module
from phoenix.models.status import RetimerStatus, VoltageInfo, PortStatus, InterruptStatus

router = APIRouter()


class TemperatureResponse(BaseModel):
    """Temperature reading response."""

    temperature_c: int
    status: str


class VoltageResponse(BaseModel):
    """Voltage readings response."""

    dvdd1_mv: int
    dvdd2_mv: int
    dvdd3_mv: int
    dvdd4_mv: int
    dvdd5_mv: int
    dvdd6_mv: int
    dvddio_mv: int


class PortStatusResponse(BaseModel):
    """Port status response."""

    port_number: int
    port_type: str
    ltssm_state: str
    link_speed: str
    link_width: int
    is_link_up: bool
    is_forwarding: bool


class StatusResponse(BaseModel):
    """Complete device status response."""

    temperature_c: int
    voltage: VoltageResponse
    ppa_status: PortStatusResponse
    ppb_status: PortStatusResponse
    global_interrupt: bool
    eq_phase_error: bool
    phy_phase_error: bool
    internal_error: bool
    firmware_version: str
    is_healthy: bool


@router.get("/{handle}/status", response_model=StatusResponse)
async def get_device_status(handle: int) -> StatusResponse:
    """Get complete device status."""
    try:
        device = app_module.get_device(handle)
        status = await device.get_status()
        return _status_to_response(status, device.device_info.firmware_version_str)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/temperature", response_model=TemperatureResponse)
async def get_temperature(handle: int) -> TemperatureResponse:
    """Get device temperature."""
    try:
        device = app_module.get_device(handle)
        temp = await device.get_temperature()
        status = "normal" if temp < 85 else "warning" if temp < 100 else "critical"
        return TemperatureResponse(temperature_c=temp, status=status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/voltage", response_model=VoltageResponse)
async def get_voltage(handle: int) -> VoltageResponse:
    """Get voltage levels."""
    try:
        device = app_module.get_device(handle)
        voltage = await device.get_voltage_info()
        return VoltageResponse(
            dvdd1_mv=voltage.dvdd1_mv,
            dvdd2_mv=voltage.dvdd2_mv,
            dvdd3_mv=voltage.dvdd3_mv,
            dvdd4_mv=voltage.dvdd4_mv,
            dvdd5_mv=voltage.dvdd5_mv,
            dvdd6_mv=voltage.dvdd6_mv,
            dvddio_mv=voltage.dvddio_mv,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{handle}/ports/{port}", response_model=PortStatusResponse)
async def get_port_status(handle: int, port: int) -> PortStatusResponse:
    """Get status for a specific port (0=PPA, 1=PPB)."""
    if port not in [0, 1]:
        raise HTTPException(status_code=400, detail="Port must be 0 (PPA) or 1 (PPB)")

    try:
        device = app_module.get_device(handle)
        status = await device.get_status()
        port_status = status.ppa_status if port == 0 else status.ppb_status
        return _port_to_response(port_status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _port_to_response(port: PortStatus) -> PortStatusResponse:
    """Convert PortStatus to response model."""
    return PortStatusResponse(
        port_number=port.port_number,
        port_type=port.port_type.name,
        ltssm_state=port.current_ltssm_state.name,
        link_speed=port.current_link_speed.name,
        link_width=port.current_link_width,
        is_link_up=port.is_link_up,
        is_forwarding=port.is_forwarding,
    )


def _status_to_response(status: RetimerStatus, fw_version: str) -> StatusResponse:
    """Convert RetimerStatus to response model."""
    return StatusResponse(
        temperature_c=status.temperature_c,
        voltage=VoltageResponse(
            dvdd1_mv=status.voltage_info.dvdd1_mv,
            dvdd2_mv=status.voltage_info.dvdd2_mv,
            dvdd3_mv=status.voltage_info.dvdd3_mv,
            dvdd4_mv=status.voltage_info.dvdd4_mv,
            dvdd5_mv=status.voltage_info.dvdd5_mv,
            dvdd6_mv=status.voltage_info.dvdd6_mv,
            dvddio_mv=status.voltage_info.dvddio_mv,
        ),
        ppa_status=_port_to_response(status.ppa_status),
        ppb_status=_port_to_response(status.ppb_status),
        global_interrupt=status.interrupt_status.global_interrupt,
        eq_phase_error=status.interrupt_status.eq_phase_error,
        phy_phase_error=status.interrupt_status.phy_phase_error,
        internal_error=status.interrupt_status.internal_error,
        firmware_version=fw_version,
        is_healthy=status.is_healthy,
    )
