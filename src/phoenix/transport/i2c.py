"""
I2C/SMBus transport implementation for Broadcom Vantage retimer.

Supports multiple USB-to-I2C adapters (FTDI, Aardvark) through an
abstract adapter interface.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

from phoenix.exceptions import (
    AdapterInitError,
    AdapterNotFoundError,
    I2CReadError,
    I2CWriteError,
    PECMismatchError,
    TimeoutError,
    TransportError,
)
from phoenix.protocol.chip_profile import load_profile
from phoenix.protocol.enums import RegisterAccessType
from phoenix.protocol.smbus_commands import (
    decode_read_response_16,
    decode_read_response_32,
    encode_read_register_16,
    encode_read_register_32,
    encode_write_register_16,
    encode_write_register_32,
)
from phoenix.transport.base import (
    I2CConfig,
    Transport,
    TransportConfig,
    TransportFactory,
    TransportState,
)
from phoenix.utils.crc import calculate_smbus_pec
from phoenix.utils.logging import get_logger

logger = get_logger(__name__)


class I2CAdapter(ABC):
    """Abstract interface for USB-to-I2C adapters."""

    @abstractmethod
    def open(self, port: int = 0) -> None:
        """Open the adapter."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the adapter."""
        ...

    @abstractmethod
    def configure(self, speed_khz: int) -> None:
        """Configure I2C bus speed."""
        ...

    @abstractmethod
    def write(self, address: int, data: bytes) -> None:
        """Write data to I2C slave."""
        ...

    @abstractmethod
    def read(self, address: int, length: int) -> bytes:
        """Read data from I2C slave."""
        ...

    @abstractmethod
    def write_read(self, address: int, write_data: bytes, read_length: int) -> bytes:
        """Write then read in a single transaction (repeated start)."""
        ...


class FTDIAdapter(I2CAdapter):
    """FTDI USB-to-I2C adapter implementation using pyftdi."""

    def __init__(self):
        self._controller = None
        self._i2c = None

    def open(self, port: int = 0) -> None:
        """Open FTDI adapter."""
        try:
            from pyftdi.i2c import I2cController

            self._controller = I2cController()
            # Default FTDI URL format
            url = f"ftdi://ftdi:232h:{port}/1"
            self._controller.configure(url)
            logger.info("ftdi_adapter_opened", port=port)
        except ImportError as e:
            raise AdapterInitError("FTDI", "pyftdi package not installed") from e
        except Exception as e:
            raise AdapterInitError("FTDI", str(e)) from e

    def close(self) -> None:
        """Close FTDI adapter."""
        if self._controller:
            self._controller.terminate()
            self._controller = None
            self._i2c = None
            logger.info("ftdi_adapter_closed")

    def configure(self, speed_khz: int) -> None:
        """Configure I2C bus speed."""
        if self._controller:
            # pyftdi uses Hz
            self._controller.configure(frequency=speed_khz * 1000)
            logger.debug("ftdi_speed_configured", speed_khz=speed_khz)

    def _get_port(self, address: int):
        """Get I2C port for the given address."""
        if not self._controller:
            raise TransportError("Adapter not open")
        return self._controller.get_port(address)

    def write(self, address: int, data: bytes) -> None:
        """Write data to I2C slave."""
        port = self._get_port(address)
        port.write(data)

    def read(self, address: int, length: int) -> bytes:
        """Read data from I2C slave."""
        port = self._get_port(address)
        return bytes(port.read(length))

    def write_read(self, address: int, write_data: bytes, read_length: int) -> bytes:
        """Write then read in a single transaction."""
        port = self._get_port(address)
        return bytes(port.exchange(write_data, read_length))


class MockAdapter(I2CAdapter):
    """Mock adapter for testing without hardware."""

    def __init__(self):
        self._registers: dict[int, int] = {}
        self._is_open = False

    def open(self, port: int = 0) -> None:
        self._is_open = True
        logger.info("mock_adapter_opened", port=port)

    def close(self) -> None:
        self._is_open = False
        logger.info("mock_adapter_closed")

    def configure(self, speed_khz: int) -> None:
        logger.debug("mock_speed_configured", speed_khz=speed_khz)

    def write(self, address: int, data: bytes) -> None:
        if not self._is_open:
            raise TransportError("Adapter not open")
        # Parse as register write
        if len(data) >= 4:
            reg_addr = (data[1] << 8) | data[2]
            if len(data) >= 6:
                value = data[3] | (data[4] << 8) | (data[5] << 16) | (data[6] << 24)
            else:
                value = data[3] | (data[4] << 8)
            self._registers[reg_addr] = value
            logger.debug("mock_write", address=address, reg=hex(reg_addr), value=hex(value))

    def read(self, address: int, length: int) -> bytes:
        if not self._is_open:
            raise TransportError("Adapter not open")
        return bytes(length)

    def write_read(self, address: int, write_data: bytes, read_length: int) -> bytes:
        if not self._is_open:
            raise TransportError("Adapter not open")
        # Parse register address from write data
        if len(write_data) >= 3:
            reg_addr = (write_data[1] << 8) | write_data[2]
            value = self._registers.get(reg_addr, 0)
            result = bytes([
                value & 0xFF,
                (value >> 8) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 24) & 0xFF,
            ])
            logger.debug("mock_read", address=address, reg=hex(reg_addr), value=hex(value))
            return result[:read_length]
        return bytes(read_length)

    def set_register(self, address: int, value: int) -> None:
        """Set a register value (for testing)."""
        self._registers[address] = value


class I2CTransport(Transport):
    """I2C/SMBus transport implementation."""

    def __init__(self, config: I2CConfig, adapter: Optional[I2CAdapter] = None):
        super().__init__(config)
        self._config: I2CConfig = config
        self._adapter = adapter
        self._lock = asyncio.Lock()

    @property
    def access_type(self) -> RegisterAccessType:
        return RegisterAccessType.SMBUS

    async def connect(self) -> None:
        """Connect to the I2C bus via USB adapter."""
        if self._state == TransportState.CONNECTED:
            return

        self._state = TransportState.CONNECTING
        try:
            # Create adapter if not provided
            if self._adapter is None:
                self._adapter = FTDIAdapter()

            # Open and configure
            self._adapter.open(self._config.adapter_port)
            self._adapter.configure(self._config.bus_speed_khz)

            self._state = TransportState.CONNECTED
            logger.info(
                "i2c_connected",
                device_address=hex(self._config.device_address),
                speed_khz=self._config.bus_speed_khz,
            )
        except Exception as e:
            self._state = TransportState.ERROR
            raise

    async def disconnect(self) -> None:
        """Disconnect from the I2C bus."""
        if self._adapter:
            self._adapter.close()
            self._adapter = None
        self._state = TransportState.DISCONNECTED
        logger.info("i2c_disconnected")

    async def read_register_16(self, address: int) -> int:
        """Read a 16-bit register."""
        async with self._lock:
            return await self._do_read_16(address)

    async def write_register_16(self, address: int, value: int) -> None:
        """Write a 16-bit register."""
        async with self._lock:
            await self._do_write_16(address, value)

    async def read_register_32(self, address: int) -> int:
        """Read a 32-bit register."""
        async with self._lock:
            return await self._do_read_32(address)

    async def write_register_32(self, address: int, value: int) -> None:
        """Write a 32-bit register."""
        async with self._lock:
            await self._do_write_32(address, value)

    async def read_block(self, address: int, length: int) -> bytes:
        """Read a block of data."""
        async with self._lock:
            return await self._do_read_block(address, length)

    async def write_block(self, address: int, data: bytes) -> None:
        """Write a block of data."""
        async with self._lock:
            await self._do_write_block(address, data)

    async def _do_read_16(self, address: int) -> int:
        """Internal 16-bit read implementation."""
        cmd, addr_bytes = encode_read_register_16(address, self._config.pec_enabled)

        for attempt in range(self._config.retry_count):
            try:
                # Build command packet
                packet = bytes([cmd]) + addr_bytes
                self._update_stats_tx(len(packet))

                # Write command and read response
                response = self._adapter.write_read(
                    self._config.device_address,
                    packet,
                    3 if self._config.pec_enabled else 2,
                )
                self._update_stats_rx(len(response))

                # Verify PEC if enabled
                if self._config.pec_enabled:
                    expected_pec = calculate_smbus_pec(
                        self._config.device_address,
                        cmd,
                        addr_bytes,
                        response[:2],
                        is_read=True,
                    )
                    if response[2] != expected_pec:
                        self._update_stats_pec_failure()
                        raise PECMismatchError(expected_pec, response[2])

                return decode_read_response_16(response)

            except PECMismatchError:
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)  # Brief delay before retry
                    continue
                raise
            except Exception as e:
                self._update_stats_error()
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)
                    continue
                raise I2CReadError(address, 2, str(e)) from e

        raise I2CReadError(address, 2, "Max retries exceeded")

    async def _do_write_16(self, address: int, value: int) -> None:
        """Internal 16-bit write implementation."""
        cmd, data = encode_write_register_16(address, value, self._config.pec_enabled)

        for attempt in range(self._config.retry_count):
            try:
                # Build command packet
                packet = bytes([cmd]) + data

                # Add PEC if enabled
                if self._config.pec_enabled:
                    pec = calculate_smbus_pec(
                        self._config.device_address, cmd, data, is_read=False
                    )
                    packet += bytes([pec])

                self._update_stats_tx(len(packet))
                self._adapter.write(self._config.device_address, packet)
                return

            except Exception as e:
                self._update_stats_error()
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)
                    continue
                raise I2CWriteError(address, data, str(e)) from e

        raise I2CWriteError(address, data, "Max retries exceeded")

    async def _do_read_32(self, address: int) -> int:
        """Internal 32-bit read implementation."""
        cmd, addr_bytes = encode_read_register_32(address, self._config.pec_enabled)

        for attempt in range(self._config.retry_count):
            try:
                # Build command packet
                packet = bytes([cmd]) + addr_bytes
                self._update_stats_tx(len(packet))

                # Write command and read response
                response = self._adapter.write_read(
                    self._config.device_address,
                    packet,
                    5 if self._config.pec_enabled else 4,
                )
                self._update_stats_rx(len(response))

                # Verify PEC if enabled
                if self._config.pec_enabled:
                    expected_pec = calculate_smbus_pec(
                        self._config.device_address,
                        cmd,
                        addr_bytes,
                        response[:4],
                        is_read=True,
                    )
                    if response[4] != expected_pec:
                        self._update_stats_pec_failure()
                        raise PECMismatchError(expected_pec, response[4])

                return decode_read_response_32(response)

            except PECMismatchError:
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)
                    continue
                raise
            except Exception as e:
                self._update_stats_error()
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)
                    continue
                raise I2CReadError(address, 4, str(e)) from e

        raise I2CReadError(address, 4, "Max retries exceeded")

    async def _do_write_32(self, address: int, value: int) -> None:
        """Internal 32-bit write implementation."""
        cmd, data = encode_write_register_32(address, value, self._config.pec_enabled)

        for attempt in range(self._config.retry_count):
            try:
                # Build command packet
                packet = bytes([cmd]) + data

                # Add PEC if enabled
                if self._config.pec_enabled:
                    pec = calculate_smbus_pec(
                        self._config.device_address, cmd, data, is_read=False
                    )
                    packet += bytes([pec])

                self._update_stats_tx(len(packet))
                self._adapter.write(self._config.device_address, packet)
                return

            except Exception as e:
                self._update_stats_error()
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    await asyncio.sleep(0.001)
                    continue
                raise I2CWriteError(address, data, str(e)) from e

        raise I2CWriteError(address, data, "Max retries exceeded")

    async def _do_read_block(self, address: int, length: int) -> bytes:
        """Internal block read implementation."""
        # Read in chunks of block_size
        result = bytearray()
        offset = address
        remaining = length

        while remaining > 0:
            chunk_size = min(remaining, self._config.block_size)

            cmds = load_profile().smbus_commands
            cmd = (
                cmds["PROCESS_BLOCK_PEC"]
                if self._config.pec_enabled
                else cmds["PROCESS_BLOCK"]
            )

            # Build read request: offset (4 bytes) + length (1 byte)
            req_data = bytes([
                offset & 0xFF,
                (offset >> 8) & 0xFF,
                (offset >> 16) & 0xFF,
                (offset >> 24) & 0xFF,
                chunk_size,
            ])

            packet = bytes([cmd, len(req_data)]) + req_data
            self._update_stats_tx(len(packet))

            # Read response
            response = self._adapter.write_read(
                self._config.device_address,
                packet,
                chunk_size + (2 if self._config.pec_enabled else 1),  # +1 for length byte
            )
            self._update_stats_rx(len(response))

            # Extract data (skip length byte)
            chunk_data = response[1 : 1 + chunk_size]
            result.extend(chunk_data)

            offset += chunk_size
            remaining -= chunk_size

        return bytes(result)

    async def _do_write_block(self, address: int, data: bytes) -> None:
        """Internal block write implementation."""
        # Write in chunks of block_size
        offset = address
        remaining = len(data)
        data_offset = 0

        while remaining > 0:
            chunk_size = min(remaining, self._config.block_size - 5)  # Reserve space for header

            cmds = load_profile().smbus_commands
            cmd = (
                cmds["WR_BLOCK_PEC"]
                if self._config.pec_enabled
                else cmds["WR_BLOCK"]
            )

            # Build write request: offset (4 bytes) + data
            chunk_data = data[data_offset : data_offset + chunk_size]
            req_data = bytes([
                offset & 0xFF,
                (offset >> 8) & 0xFF,
                (offset >> 16) & 0xFF,
                (offset >> 24) & 0xFF,
            ]) + chunk_data

            packet = bytes([cmd, len(req_data)]) + req_data

            # Add PEC if enabled
            if self._config.pec_enabled:
                pec = calculate_smbus_pec(
                    self._config.device_address, cmd, req_data, is_read=False
                )
                packet += bytes([pec])

            self._update_stats_tx(len(packet))
            self._adapter.write(self._config.device_address, packet)

            offset += chunk_size
            remaining -= chunk_size
            data_offset += chunk_size


# Register transport with factory
TransportFactory.register("i2c", I2CTransport)
