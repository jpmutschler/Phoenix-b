"""Pytest configuration and fixtures for Phoenix tests."""

import pytest
import asyncio
from typing import Generator

from phoenix.transport.i2c import MockAdapter, I2CTransport
from phoenix.transport.base import I2CConfig
from phoenix.models.device_info import DeviceInfo
from phoenix.protocol.chip_profile import ChipProfile, load_profile
from phoenix.protocol.enums import HandleType, MaxDataRate


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def chip_profile() -> ChipProfile:
    """Provide the default chip profile for tests."""
    return load_profile()


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """Create a mock I2C adapter for testing."""
    adapter = MockAdapter()
    # Pre-populate with default register values
    adapter.set_register(0x0000, 0xD6FC0003)  # GLOBAL_PARAM0
    adapter.set_register(0x0004, 0x14E467A0)  # GLOBAL_PARAM1 (Broadcom vendor ID)
    adapter.set_register(0x4000, 0x00010123)  # XAGENT_INFO_0 (FW version)
    return adapter


@pytest.fixture
def mock_i2c_config() -> I2CConfig:
    """Create I2C configuration for testing."""
    return I2CConfig(
        device_address=0x50,
        adapter_port=0,
        bus_speed_khz=400,
        timeout_ms=1000,
        retry_count=3,
        pec_enabled=False,  # Disable PEC for mock testing
    )


@pytest.fixture
def mock_transport(mock_adapter: MockAdapter, mock_i2c_config: I2CConfig) -> I2CTransport:
    """Create a mock I2C transport for testing."""
    return I2CTransport(mock_i2c_config, adapter=mock_adapter)


@pytest.fixture
def sample_device_info() -> DeviceInfo:
    """Create sample device info for testing."""
    return DeviceInfo(
        product_handle=1,
        handle_type=HandleType.RETIMER_I2C,
        pci_vendor_id=0x14E4,
        pci_device_id=0x8567,
        revision_id=0xA0,
        firmware_version=0x0123,
        device_address=0x50,
        max_speed=MaxDataRate.GEN6_64G,
    )
