"""
FastAPI application for Phoenix Retimer API.

Provides REST and WebSocket interfaces for the browser-based UX.
"""

from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from phoenix.api.routes import devices, config, status, diagnostics
from phoenix.core.discovery import DeviceDiscovery
from phoenix.core.device import RetimerDevice
from phoenix.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

# Global state for device management
_discovery: Optional[DeviceDiscovery] = None
_connected_devices: Dict[int, RetimerDevice] = {}


def get_discovery() -> DeviceDiscovery:
    """Get the device discovery instance."""
    global _discovery
    if _discovery is None:
        _discovery = DeviceDiscovery()
    return _discovery


def get_device(handle: int) -> RetimerDevice:
    """Get a connected device by handle.

    Args:
        handle: Device handle

    Returns:
        RetimerDevice instance

    Raises:
        HTTPException: If device not found
    """
    if handle not in _connected_devices:
        raise HTTPException(status_code=404, detail=f"Device {handle} not connected")
    return _connected_devices[handle]


def register_device(device: RetimerDevice) -> None:
    """Register a connected device."""
    _connected_devices[device.device_info.product_handle] = device


def unregister_device(handle: int) -> None:
    """Unregister a device."""
    _connected_devices.pop(handle, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    setup_logging()
    logger.info("phoenix_api_starting")
    yield
    # Cleanup: disconnect all devices
    for device in list(_connected_devices.values()):
        try:
            await device.disconnect()
        except Exception as e:
            logger.warning("cleanup_error", error=str(e))
    _connected_devices.clear()
    logger.info("phoenix_api_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Phoenix Retimer API",
        description="REST API for Broadcom Vantage PCIe Gen6 Retimer control and monitoring",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS for browser access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
    app.include_router(config.router, prefix="/api/devices", tags=["Configuration"])
    app.include_router(status.router, prefix="/api/devices", tags=["Status"])
    app.include_router(diagnostics.router, prefix="/api/devices", tags=["Diagnostics"])

    @app.get("/api/", tags=["Root"])
    async def root():
        """API root endpoint."""
        return {
            "name": "Phoenix Retimer API",
            "version": "0.1.0",
            "status": "running",
            "connected_devices": len(_connected_devices),
        }

    @app.get("/health", tags=["Health"])
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}

    return app


def create_app_with_ui() -> FastAPI:
    """Create FastAPI app with NiceGUI dashboard mounted.

    NiceGUI owns '/' and serves the browser UI.
    REST API continues to work at '/api/devices/'.

    Returns:
        Configured FastAPI application with NiceGUI UI.
    """
    fastapi_app = create_app()
    from phoenix.ui import setup_ui
    setup_ui(fastapi_app)
    return fastapi_app


# Create default app instance
app = create_app()
