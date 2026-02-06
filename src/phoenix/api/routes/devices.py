"""
Device management API routes.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from phoenix.api import app as app_module
from phoenix.core.device import RetimerDevice
from phoenix.models.device_info import DeviceInfo
from phoenix.protocol.enums import HandleType
from phoenix.transport.base import I2CConfig, UARTConfig
from phoenix.transport.i2c import I2CTransport
from phoenix.transport.uart import UARTTransport

router = APIRouter()


class DiscoveryRequest(BaseModel):
    """Request to discover devices."""

    transport_type: str = Field(
        default="i2c", description="Transport type (i2c or uart)"
    )
    adapter_port: int = Field(default=0, description="USB adapter port (for I2C)")
    addresses: Optional[List[int]] = Field(
        default=None, description="I2C addresses to scan"
    )
    bus_speed_khz: int = Field(default=400, description="I2C bus speed in kHz")
    serial_port: Optional[str] = Field(
        default=None, description="Serial port for UART"
    )
    baud_rate: int = Field(default=115200, description="Baud rate for UART")


class ConnectRequest(BaseModel):
    """Request to connect to a device."""

    transport_type: str = Field(
        default="i2c", description="Transport type (i2c or uart)"
    )
    device_address: int = Field(default=0x50, description="I2C device address")
    adapter_port: int = Field(default=0, description="USB adapter port")
    bus_speed_khz: int = Field(default=400, description="I2C bus speed")
    serial_port: Optional[str] = Field(default=None, description="Serial port for UART")
    baud_rate: int = Field(default=115200, description="Baud rate for UART")


class DeviceResponse(BaseModel):
    """Device information response."""

    handle: int
    vendor_id: str
    device_id: str
    revision_id: int
    firmware_version: str
    device_address: int
    max_speed: str
    transport_type: str


@router.post("/discover", response_model=List[DeviceResponse])
async def discover_devices(request: DiscoveryRequest) -> List[DeviceResponse]:
    """Discover retimer devices on the specified bus.

    Returns list of discovered devices.
    """
    discovery = app_module.get_discovery()

    try:
        if request.transport_type.lower() == "i2c":
            devices = await discovery.discover_i2c(
                adapter_port=request.adapter_port,
                addresses=request.addresses,
                bus_speed_khz=request.bus_speed_khz,
            )
        elif request.transport_type.lower() == "uart":
            if not request.serial_port:
                raise HTTPException(
                    status_code=400, detail="serial_port required for UART discovery"
                )
            devices = await discovery.discover_uart(
                port=request.serial_port,
                baud_rate=request.baud_rate,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown transport type: {request.transport_type}"
            )

        return [_device_to_response(d) for d in devices]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[DeviceResponse])
async def list_devices() -> List[DeviceResponse]:
    """List all discovered devices."""
    discovery = app_module.get_discovery()
    return [_device_to_response(d) for d in discovery.devices]


@router.get("/{handle}", response_model=DeviceResponse)
async def get_device(handle: int) -> DeviceResponse:
    """Get device information by handle."""
    discovery = app_module.get_discovery()
    device = discovery.get_device_by_handle(handle)

    if device is None:
        raise HTTPException(status_code=404, detail=f"Device {handle} not found")

    return _device_to_response(device)


@router.post("/{handle}/connect")
async def connect_device(handle: int) -> dict:
    """Connect to a discovered device."""
    discovery = app_module.get_discovery()
    device_info = discovery.get_device_by_handle(handle)

    if device_info is None:
        raise HTTPException(status_code=404, detail=f"Device {handle} not found")

    try:
        device = RetimerDevice(device_info)
        await device.connect()
        app_module.register_device(device)
        return {"status": "connected", "handle": handle}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connect", response_model=DeviceResponse)
async def connect_new_device(request: ConnectRequest) -> DeviceResponse:
    """Connect to a device directly (without discovery)."""
    try:
        if request.transport_type.lower() == "i2c":
            device = await RetimerDevice.from_i2c(
                address=request.device_address,
                adapter_port=request.adapter_port,
                bus_speed_khz=request.bus_speed_khz,
            )
        elif request.transport_type.lower() == "uart":
            if not request.serial_port:
                raise HTTPException(
                    status_code=400, detail="serial_port required for UART"
                )
            device = await RetimerDevice.from_uart(
                port=request.serial_port,
                baud_rate=request.baud_rate,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown transport type: {request.transport_type}"
            )

        app_module.register_device(device)
        return _device_to_response(device.device_info)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{handle}/disconnect")
async def disconnect_device(handle: int) -> dict:
    """Disconnect from a device."""
    try:
        device = app_module.get_device(handle)
        await device.disconnect()
        app_module.unregister_device(handle)
        return {"status": "disconnected", "handle": handle}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _device_to_response(device: DeviceInfo) -> DeviceResponse:
    """Convert DeviceInfo to response model."""
    return DeviceResponse(
        handle=device.product_handle,
        vendor_id=device.vendor_id_str,
        device_id=device.device_id_str,
        revision_id=device.revision_id,
        firmware_version=device.firmware_version_str,
        device_address=device.device_address,
        max_speed=device.max_speed.name,
        transport_type="I2C" if device.handle_type == HandleType.RETIMER_I2C else "UART",
    )
