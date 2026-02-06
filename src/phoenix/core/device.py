"""Main RetimerDevice class for controlling Broadcom Vantage retimers.

Provides a high-level API for device operations including configuration,
status monitoring, and diagnostics.
"""

from typing import Optional, Union

from phoenix.exceptions import (
    DeviceNotFoundError,
    InvalidParameterError,
    PhoenixError,
)
from phoenix.models.device_info import DeviceInfo
from phoenix.models.status import RetimerStatus, PortStatus, VoltageInfo, InterruptStatus
from phoenix.models.configuration import DeviceConfiguration, ConfigurationUpdate
from phoenix.protocol.chip_profile import ChipProfile, load_profile
from phoenix.protocol.enums import (
    BifurcationMode,
    ClockingMode,
    HandleType,
    LTSSMState,
    MaxDataRate,
    PortOrientation,
    ResetType,
    ConfigOption,
    ForwardingMode,
    LinkState,
)
from phoenix.protocol.register_maps import RegisterAccess
from phoenix.transport.base import Transport, I2CConfig, UARTConfig
from phoenix.transport.i2c import I2CTransport
from phoenix.transport.uart import UARTTransport
from phoenix.utils.logging import get_logger

logger = get_logger(__name__)


class RetimerDevice:
    """High-level interface for a Broadcom Vantage retimer device.

    This class provides the main API for interacting with a retimer device,
    including configuration, status monitoring, and diagnostic operations.
    """

    def __init__(
        self,
        device_info: DeviceInfo,
        transport: Optional[Transport] = None,
        profile: Optional[ChipProfile] = None,
    ):
        """Initialize RetimerDevice.

        Args:
            device_info: Device information from discovery
            transport: Optional transport instance (created automatically if None)
            profile: Optional chip profile (defaults to BCM85667)
        """
        self._device_info = device_info
        self._transport = transport
        self._profile = profile or load_profile()
        self._connected = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return self._device_info

    @property
    def is_connected(self) -> bool:
        """Check if device is connected."""
        return self._connected and self._transport is not None

    @classmethod
    async def from_i2c(
        cls,
        address: int = 0x50,
        adapter_port: int = 0,
        bus_speed_khz: int = 400,
    ) -> "RetimerDevice":
        """Create a RetimerDevice connected via I2C.

        Args:
            address: I2C device address
            adapter_port: USB adapter port
            bus_speed_khz: I2C bus speed

        Returns:
            Connected RetimerDevice instance
        """
        config = I2CConfig(
            device_address=address,
            adapter_port=adapter_port,
            bus_speed_khz=bus_speed_khz,
        )
        transport = I2CTransport(config)

        # Create placeholder device info (will be populated on connect)
        device_info = DeviceInfo(
            product_handle=1,
            handle_type=HandleType.RETIMER_I2C,
            device_address=address,
        )

        device = cls(device_info, transport)
        await device.connect()
        return device

    @classmethod
    async def from_uart(
        cls,
        port: str,
        baud_rate: int = 115200,
    ) -> "RetimerDevice":
        """Create a RetimerDevice connected via UART.

        Args:
            port: Serial port name
            baud_rate: Baud rate

        Returns:
            Connected RetimerDevice instance
        """
        config = UARTConfig(port=port, baud_rate=baud_rate)
        transport = UARTTransport(config)

        device_info = DeviceInfo(
            product_handle=1,
            handle_type=HandleType.RETIMER_UART,
        )

        device = cls(device_info, transport)
        await device.connect()
        return device

    async def connect(self) -> None:
        """Connect to the device.

        Creates transport if needed and reads device identification.
        """
        if self._connected:
            return

        # Create transport if not provided
        if self._transport is None:
            if self._device_info.handle_type == HandleType.RETIMER_I2C:
                config = I2CConfig(device_address=self._device_info.device_address)
                self._transport = I2CTransport(config)
            elif self._device_info.handle_type == HandleType.RETIMER_UART:
                config = UARTConfig()
                self._transport = UARTTransport(config)
            else:
                raise InvalidParameterError(
                    "handle_type", self._device_info.handle_type, "Unsupported handle type"
                )

        await self._transport.connect()
        self._connected = True

        # Read device identification
        await self._read_device_info()

        logger.info(
            "device_connected",
            handle=self._device_info.product_handle,
            vendor=self._device_info.vendor_id_str,
            device=self._device_info.device_id_str,
            firmware=self._device_info.firmware_version_str,
        )

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self._transport:
            await self._transport.disconnect()
        self._connected = False
        logger.info("device_disconnected", handle=self._device_info.product_handle)

    async def _read_device_info(self) -> None:
        """Read and update device identification info."""
        global_param1 = self._profile.get_register("GLOBAL_PARAM1")
        xagent_info_0 = self._profile.get_register("XAGENT_INFO_0")
        global_param0 = self._profile.get_register("GLOBAL_PARAM0")

        # Read GLOBAL_PARAM1 for IDs
        param1 = await self._transport.read_register_32(global_param1.address)
        self._device_info.pci_vendor_id = RegisterAccess.get_field_value(
            global_param1, param1, "VENDOR_ID"
        )
        self._device_info.pci_device_id = RegisterAccess.get_field_value(
            global_param1, param1, "DEVICE_ID"
        )
        self._device_info.revision_id = RegisterAccess.get_field_value(
            global_param1, param1, "REVISION_ID"
        )

        # Read firmware version
        xagent = await self._transport.read_register_32(xagent_info_0.address)
        self._device_info.firmware_version = RegisterAccess.get_field_value(
            xagent_info_0, xagent, "FW_VERSION"
        )

        # Read max data rate
        param0 = await self._transport.read_register_32(global_param0.address)
        max_rate = RegisterAccess.get_field_value(global_param0, param0, "MAX_DATA_RATE")
        if max_rate > 0:
            self._device_info.max_speed = MaxDataRate(max_rate)

    async def get_status(self) -> RetimerStatus:
        """Get complete device status.

        Returns:
            RetimerStatus with all status information
        """
        self._ensure_connected()

        status = RetimerStatus()

        # Read temperature
        status.temperature_c = await self.get_temperature()

        # Read voltages
        status.voltage_info = await self.get_voltage_info()

        # Read port status
        status.ppa_status = await self._get_port_status(0)
        status.ppb_status = await self._get_port_status(1)

        # Read interrupt status
        status.interrupt_status = await self.get_interrupt_status()

        # Firmware version from cached info
        status.firmware_version = self._device_info.firmware_version

        return status

    async def get_temperature(self) -> int:
        """Get device temperature in degrees Celsius.

        Returns:
            Temperature in degrees C
        """
        self._ensure_connected()
        temperature = self._profile.get_register("TEMPERATURE")
        temp_reg = await self._transport.read_register_32(temperature.address)
        temp = RegisterAccess.get_field_value(temperature, temp_reg, "TEMPERATURE")
        return temp

    async def get_voltage_info(self) -> VoltageInfo:
        """Get voltage levels.

        Returns:
            VoltageInfo with all voltage readings
        """
        self._ensure_connected()

        return VoltageInfo(
            dvdd1_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD1").address
            ),
            dvdd2_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD2").address
            ),
            dvdd3_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD3").address
            ),
            dvdd4_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD4").address
            ),
            dvdd5_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD5").address
            ),
            dvdd6_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDD6").address
            ),
            dvddio_mv=await self._transport.read_register_32(
                self._profile.get_register("VOLTAGE_DVDDIO").address
            ),
        )

    async def get_interrupt_status(self) -> InterruptStatus:
        """Get interrupt status.

        Returns:
            InterruptStatus with all interrupt flags
        """
        self._ensure_connected()
        global_intr = self._profile.get_register("GLOBAL_INTR")
        intr_reg = await self._transport.read_register_32(global_intr.address)

        return InterruptStatus(
            global_interrupt=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "INTR_STS")
            ),
            eq_phase_error=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "EQ_PHASE_ERR_STS")
            ),
            phy_phase_error=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "PHY_PHASE_ERR_STS")
            ),
            internal_error=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "RTMR_INT_ERR_STS")
            ),
        )

    async def _get_port_status(self, port: int) -> PortStatus:
        """Get status for a pseudo port.

        Args:
            port: Port number (0=PPA, 1=PPB)

        Returns:
            PortStatus for the specified port
        """
        reg_name = "PPA_LTSSM_STATE" if port == 0 else "PPB_LTSSM_STATE"
        reg = self._profile.get_register(reg_name)
        ltssm_reg = await self._transport.read_register_32(reg.address)

        state = RegisterAccess.get_field_value(reg, ltssm_reg, "CURRENT_STATE")
        speed = RegisterAccess.get_field_value(reg, ltssm_reg, "LINK_SPEED")
        width = RegisterAccess.get_field_value(reg, ltssm_reg, "LINK_WIDTH")
        forwarding = RegisterAccess.get_field_value(reg, ltssm_reg, "FORWARDING_MODE")

        return PortStatus(
            port_number=port,
            current_ltssm_state=LTSSMState(state) if state in [e.value for e in LTSSMState] else LTSSMState.DETECT,
            current_link_speed=MaxDataRate(speed) if speed > 0 else MaxDataRate.RESERVED,
            current_link_width=width,
            forwarding_mode=ForwardingMode.ENABLED if forwarding else ForwardingMode.DISABLED,
            link_state=LinkState.UP if forwarding and width > 0 else LinkState.DOWN,
        )

    async def get_configuration(self) -> DeviceConfiguration:
        """Get current device configuration.

        Returns:
            DeviceConfiguration with current settings
        """
        self._ensure_connected()

        global_param0 = self._profile.get_register("GLOBAL_PARAM0")
        global_intr = self._profile.get_register("GLOBAL_INTR")

        param0 = await self._transport.read_register_32(global_param0.address)

        bifurcation = RegisterAccess.get_field_value(global_param0, param0, "BIFURCATION")
        max_rate = RegisterAccess.get_field_value(global_param0, param0, "MAX_DATA_RATE")
        clk_mode = RegisterAccess.get_field_value(global_param0, param0, "CLK_MODE")
        port_orient = RegisterAccess.get_field_value(global_param0, param0, "PORT_ORIEN_METHOD")

        # Read interrupt configuration
        intr_reg = await self._transport.read_register_32(global_intr.address)

        from phoenix.models.configuration import InterruptConfiguration

        intr_config = InterruptConfiguration(
            global_interrupt_enable=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "INTR_EN")
            ),
            eq_phase_error_enable=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "EQ_PHASE_ERR_EN")
            ),
            phy_phase_error_enable=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "PHY_PHASE_ERR_EN")
            ),
            internal_error_enable=bool(
                RegisterAccess.get_field_value(global_intr, intr_reg, "RTMR_INT_ERR_EN")
            ),
        )

        return DeviceConfiguration(
            bifurcation_mode=BifurcationMode(bifurcation),
            max_data_rate=MaxDataRate(max_rate) if max_rate > 0 else MaxDataRate.GEN6_64G,
            clocking_mode=ClockingMode(clk_mode),
            port_orientation=PortOrientation(port_orient),
            interrupt_config=intr_config,
        )

    async def set_configuration(self, update: ConfigurationUpdate) -> None:
        """Update device configuration.

        Args:
            update: Configuration values to update (None values are skipped)
        """
        self._ensure_connected()

        global_param0 = self._profile.get_register("GLOBAL_PARAM0")

        # Read current value
        param0 = await self._transport.read_register_32(global_param0.address)

        # Apply updates
        if update.bifurcation_mode is not None:
            param0 = RegisterAccess.set_field_value(
                global_param0, param0, "BIFURCATION", update.bifurcation_mode.value
            )

        if update.max_data_rate is not None:
            param0 = RegisterAccess.set_field_value(
                global_param0, param0, "MAX_DATA_RATE", update.max_data_rate.value
            )

        if update.clocking_mode is not None:
            param0 = RegisterAccess.set_field_value(
                global_param0, param0, "CLK_MODE", update.clocking_mode.value
            )

        if update.port_orientation is not None:
            param0 = RegisterAccess.set_field_value(
                global_param0, param0, "PORT_ORIEN_METHOD", update.port_orientation.value
            )

        # Write updated value
        await self._transport.write_register_32(global_param0.address, param0)

        logger.info(
            "configuration_updated",
            bifurcation=update.bifurcation_mode,
            max_data_rate=update.max_data_rate,
            clocking_mode=update.clocking_mode,
        )

    async def reset(self, reset_type: ResetType = ResetType.SOFT) -> None:
        """Reset the device.

        Args:
            reset_type: Type of reset to perform
        """
        self._ensure_connected()

        reset_ctrl = self._profile.get_register("RESET_CTRL")

        reset_reg = 0
        reset_reg = RegisterAccess.set_field_value(
            reset_ctrl, reset_reg, reset_type.name, 1
        )

        await self._transport.write_register_32(reset_ctrl.address, reset_reg)

        logger.info("device_reset", reset_type=reset_type.name)

    async def read_register(self, address: int, width: int = 32) -> int:
        """Read a register directly.

        Args:
            address: Register address
            width: Register width (16 or 32)

        Returns:
            Register value
        """
        self._ensure_connected()
        return await self._transport.read_register(address, width)

    async def write_register(self, address: int, value: int, width: int = 32) -> None:
        """Write a register directly.

        Args:
            address: Register address
            value: Value to write
            width: Register width (16 or 32)
        """
        self._ensure_connected()
        await self._transport.write_register(address, value, width)

    def _ensure_connected(self) -> None:
        """Raise exception if not connected."""
        if not self._connected:
            raise PhoenixError("Device not connected")

    async def __aenter__(self) -> "RetimerDevice":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()
