"""Device discovery for Broadcom Vantage retimers.

Provides functionality to discover retimer devices on I2C/SMBus
and UART interfaces.
"""

from typing import List, Optional

from phoenix.exceptions import DiscoveryError
from phoenix.models.device_info import DeviceInfo
from phoenix.protocol.chip_profile import ChipProfile, load_profile
from phoenix.protocol.enums import HandleType, MaxDataRate
from phoenix.protocol.register_maps import RegisterAccess
from phoenix.transport.base import Transport, I2CConfig, UARTConfig
from phoenix.transport.i2c import I2CTransport
from phoenix.transport.uart import UARTTransport
from phoenix.utils.logging import get_logger

logger = get_logger(__name__)


# Default I2C addresses to scan
DEFAULT_I2C_ADDRESSES = [0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57]


class DeviceDiscovery:
    """Device discovery service for retimer devices."""

    def __init__(self, profile: Optional[ChipProfile] = None):
        self._discovered_devices: List[DeviceInfo] = []
        self._handle_counter = 0
        self._profile = profile or load_profile()

    @property
    def devices(self) -> List[DeviceInfo]:
        """Return list of discovered devices."""
        return self._discovered_devices.copy()

    def clear(self) -> None:
        """Clear discovered devices list."""
        self._discovered_devices.clear()

    async def discover_i2c(
        self,
        adapter_port: int = 0,
        addresses: Optional[List[int]] = None,
        bus_speed_khz: int = 400,
    ) -> List[DeviceInfo]:
        """Discover retimer devices on I2C bus.

        Args:
            adapter_port: USB adapter port number
            addresses: List of I2C addresses to scan (default: 0x50-0x57)
            bus_speed_khz: I2C bus speed in kHz

        Returns:
            List of discovered DeviceInfo objects

        Raises:
            DiscoveryError: If discovery fails
        """
        if addresses is None:
            addresses = DEFAULT_I2C_ADDRESSES

        discovered = []
        logger.info(
            "i2c_discovery_started",
            adapter_port=adapter_port,
            addresses=[hex(a) for a in addresses],
        )

        for address in addresses:
            try:
                device = await self._probe_i2c_address(
                    adapter_port, address, bus_speed_khz
                )
                if device:
                    discovered.append(device)
                    self._discovered_devices.append(device)
                    logger.info(
                        "device_discovered",
                        address=hex(address),
                        vendor_id=device.vendor_id_str,
                        device_id=device.device_id_str,
                    )
            except Exception as e:
                logger.debug("probe_failed", address=hex(address), error=str(e))

        logger.info("i2c_discovery_complete", device_count=len(discovered))
        return discovered

    async def _probe_i2c_address(
        self, adapter_port: int, address: int, bus_speed_khz: int
    ) -> Optional[DeviceInfo]:
        """Probe a single I2C address for a retimer device.

        Args:
            adapter_port: USB adapter port
            address: I2C address to probe
            bus_speed_khz: Bus speed

        Returns:
            DeviceInfo if device found, None otherwise
        """
        config = I2CConfig(
            device_address=address,
            adapter_port=adapter_port,
            bus_speed_khz=bus_speed_khz,
            timeout_ms=500,
            retry_count=1,
            pec_enabled=True,
        )

        transport = I2CTransport(config)

        global_param1 = self._profile.get_register("GLOBAL_PARAM1")
        xagent_info_0 = self._profile.get_register("XAGENT_INFO_0")
        global_param0 = self._profile.get_register("GLOBAL_PARAM0")

        try:
            await transport.connect()

            # Read device identification registers
            param1_value = await transport.read_register_32(global_param1.address)

            # Extract vendor and device IDs
            vendor_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "VENDOR_ID"
            )
            device_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "DEVICE_ID"
            )
            revision_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "REVISION_ID"
            )

            # Verify this is a Broadcom device
            if vendor_id != self._profile.vendor_id:
                logger.debug(
                    "not_broadcom_device",
                    address=hex(address),
                    vendor_id=hex(vendor_id),
                )
                return None

            # Read firmware version
            xagent_value = await transport.read_register_32(xagent_info_0.address)
            fw_version = RegisterAccess.get_field_value(
                xagent_info_0, xagent_value, "FW_VERSION"
            )

            # Read global parameters for max speed
            param0_value = await transport.read_register_32(global_param0.address)
            max_rate = RegisterAccess.get_field_value(
                global_param0, param0_value, "MAX_DATA_RATE"
            )

            # Create device info
            self._handle_counter += 1
            device = DeviceInfo(
                product_handle=self._handle_counter,
                handle_type=HandleType.RETIMER_I2C,
                pci_vendor_id=vendor_id,
                pci_device_id=device_id,
                revision_id=revision_id,
                firmware_version=fw_version,
                device_address=address,
                max_speed=MaxDataRate(max_rate) if max_rate > 0 else MaxDataRate.GEN6_64G,
            )

            return device

        except Exception as e:
            logger.debug("probe_error", address=hex(address), error=str(e))
            return None

        finally:
            await transport.disconnect()

    async def discover_uart(
        self, port: str, baud_rate: int = 115200
    ) -> List[DeviceInfo]:
        """Discover retimer devices on UART interface.

        Args:
            port: Serial port name (e.g., "COM3" or "/dev/ttyUSB0")
            baud_rate: Baud rate for serial communication

        Returns:
            List of discovered DeviceInfo objects

        Raises:
            DiscoveryError: If discovery fails
        """
        discovered = []
        logger.info("uart_discovery_started", port=port, baud_rate=baud_rate)

        try:
            device = await self._probe_uart(port, baud_rate)
            if device:
                discovered.append(device)
                self._discovered_devices.append(device)
                logger.info(
                    "device_discovered",
                    port=port,
                    vendor_id=device.vendor_id_str,
                    device_id=device.device_id_str,
                )
        except Exception as e:
            logger.warning("uart_discovery_failed", port=port, error=str(e))
            raise DiscoveryError(f"UART discovery failed: {e}", adapter_type="UART")

        logger.info("uart_discovery_complete", device_count=len(discovered))
        return discovered

    async def _probe_uart(self, port: str, baud_rate: int) -> Optional[DeviceInfo]:
        """Probe UART interface for a retimer device.

        Args:
            port: Serial port name
            baud_rate: Baud rate

        Returns:
            DeviceInfo if device found, None otherwise
        """
        config = UARTConfig(
            port=port,
            baud_rate=baud_rate,
            timeout_ms=1000,
            retry_count=2,
        )

        transport = UARTTransport(config)

        global_param1 = self._profile.get_register("GLOBAL_PARAM1")
        xagent_info_0 = self._profile.get_register("XAGENT_INFO_0")
        global_param0 = self._profile.get_register("GLOBAL_PARAM0")

        try:
            await transport.connect()

            # Read device identification
            param1_value = await transport.read_register_32(global_param1.address)

            vendor_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "VENDOR_ID"
            )
            device_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "DEVICE_ID"
            )
            revision_id = RegisterAccess.get_field_value(
                global_param1, param1_value, "REVISION_ID"
            )

            if vendor_id != self._profile.vendor_id:
                return None

            # Read firmware version
            xagent_value = await transport.read_register_32(xagent_info_0.address)
            fw_version = RegisterAccess.get_field_value(
                xagent_info_0, xagent_value, "FW_VERSION"
            )

            # Read max speed
            param0_value = await transport.read_register_32(global_param0.address)
            max_rate = RegisterAccess.get_field_value(
                global_param0, param0_value, "MAX_DATA_RATE"
            )

            self._handle_counter += 1
            device = DeviceInfo(
                product_handle=self._handle_counter,
                handle_type=HandleType.RETIMER_UART,
                pci_vendor_id=vendor_id,
                pci_device_id=device_id,
                revision_id=revision_id,
                firmware_version=fw_version,
                device_address=0,  # Not applicable for UART
                max_speed=MaxDataRate(max_rate) if max_rate > 0 else MaxDataRate.GEN6_64G,
            )

            return device

        except Exception as e:
            logger.debug("uart_probe_error", port=port, error=str(e))
            return None

        finally:
            await transport.disconnect()

    def get_device_by_handle(self, handle: int) -> Optional[DeviceInfo]:
        """Get device info by handle.

        Args:
            handle: Device handle

        Returns:
            DeviceInfo if found, None otherwise
        """
        for device in self._discovered_devices:
            if device.product_handle == handle:
                return device
        return None

    def get_device_by_address(self, address: int) -> Optional[DeviceInfo]:
        """Get device info by I2C address.

        Args:
            address: I2C address

        Returns:
            DeviceInfo if found, None otherwise
        """
        for device in self._discovered_devices:
            if device.device_address == address:
                return device
        return None
