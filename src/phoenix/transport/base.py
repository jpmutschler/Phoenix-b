"""
Abstract base class for transport layer implementations.

Defines the interface that all transport implementations (I2C, UART, etc.) must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

from phoenix.protocol.enums import RegisterAccessType


class TransportState(IntEnum):
    """Transport connection state."""

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3


@dataclass
class TransportConfig:
    """Base configuration for transport layer."""

    device_address: int = 0x50  # Default I2C address for retimer
    timeout_ms: int = 1000
    retry_count: int = 3
    pec_enabled: bool = True  # Packet Error Checking


@dataclass
class I2CConfig(TransportConfig):
    """Configuration for I2C/SMBus transport."""

    bus_speed_khz: int = 400  # I2C bus speed in kHz
    block_size: int = 32  # SMBus block size (32 for 2.0, 64 for 3.0)
    adapter_port: int = 0  # USB adapter port number


@dataclass
class UARTConfig(TransportConfig):
    """Configuration for UART transport."""

    port: str = ""  # COM port or /dev/ttyUSB path
    baud_rate: int = 115200
    data_bits: int = 8
    stop_bits: int = 1
    parity: str = "N"  # N=None, E=Even, O=Odd
    flow_control: bool = False


@dataclass
class TransportStats:
    """Transport layer statistics."""

    bytes_sent: int = 0
    bytes_received: int = 0
    transactions: int = 0
    errors: int = 0
    retries: int = 0
    pec_failures: int = 0


class Transport(ABC):
    """Abstract base class for transport layer implementations.

    All transport implementations (I2C, UART, etc.) must inherit from this class
    and implement the abstract methods.
    """

    def __init__(self, config: TransportConfig):
        self._config = config
        self._state = TransportState.DISCONNECTED
        self._stats = TransportStats()

    @property
    def config(self) -> TransportConfig:
        """Return transport configuration."""
        return self._config

    @property
    def state(self) -> TransportState:
        """Return current connection state."""
        return self._state

    @property
    def stats(self) -> TransportStats:
        """Return transport statistics."""
        return self._stats

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._state == TransportState.CONNECTED

    @property
    @abstractmethod
    def access_type(self) -> RegisterAccessType:
        """Return the register access type for this transport."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the device.

        Raises:
            TransportError: If connection fails
            AdapterNotFoundError: If USB adapter not found
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the device."""
        ...

    @abstractmethod
    async def read_register_16(self, address: int) -> int:
        """Read a 16-bit register.

        Args:
            address: Register address (16-bit)

        Returns:
            16-bit register value

        Raises:
            TransportError: If read fails
            TimeoutError: If operation times out
        """
        ...

    @abstractmethod
    async def write_register_16(self, address: int, value: int) -> None:
        """Write a 16-bit register.

        Args:
            address: Register address (16-bit)
            value: 16-bit value to write

        Raises:
            TransportError: If write fails
            TimeoutError: If operation times out
        """
        ...

    @abstractmethod
    async def read_register_32(self, address: int) -> int:
        """Read a 32-bit register.

        Args:
            address: Register address (32-bit)

        Returns:
            32-bit register value

        Raises:
            TransportError: If read fails
            TimeoutError: If operation times out
        """
        ...

    @abstractmethod
    async def write_register_32(self, address: int, value: int) -> None:
        """Write a 32-bit register.

        Args:
            address: Register address (32-bit)
            value: 32-bit value to write

        Raises:
            TransportError: If write fails
            TimeoutError: If operation times out
        """
        ...

    @abstractmethod
    async def read_block(self, address: int, length: int) -> bytes:
        """Read a block of data.

        Args:
            address: Starting address
            length: Number of bytes to read

        Returns:
            Block of data as bytes

        Raises:
            TransportError: If read fails
            TimeoutError: If operation times out
        """
        ...

    @abstractmethod
    async def write_block(self, address: int, data: bytes) -> None:
        """Write a block of data.

        Args:
            address: Starting address
            data: Data to write

        Raises:
            TransportError: If write fails
            TimeoutError: If operation times out
        """
        ...

    async def read_register(self, address: int, width: int = 32) -> int:
        """Read a register with specified width.

        Args:
            address: Register address
            width: Register width in bits (16 or 32)

        Returns:
            Register value

        Raises:
            InvalidParameterError: If width is not 16 or 32
        """
        if width == 16:
            return await self.read_register_16(address)
        elif width == 32:
            return await self.read_register_32(address)
        else:
            from phoenix.exceptions import InvalidParameterError

            raise InvalidParameterError("width", width, "must be 16 or 32")

    async def write_register(self, address: int, value: int, width: int = 32) -> None:
        """Write a register with specified width.

        Args:
            address: Register address
            value: Value to write
            width: Register width in bits (16 or 32)

        Raises:
            InvalidParameterError: If width is not 16 or 32
        """
        if width == 16:
            await self.write_register_16(address, value)
        elif width == 32:
            await self.write_register_32(address, value)
        else:
            from phoenix.exceptions import InvalidParameterError

            raise InvalidParameterError("width", width, "must be 16 or 32")

    def reset_stats(self) -> None:
        """Reset transport statistics."""
        self._stats = TransportStats()

    def _update_stats_tx(self, byte_count: int) -> None:
        """Update statistics after transmission."""
        self._stats.bytes_sent += byte_count
        self._stats.transactions += 1

    def _update_stats_rx(self, byte_count: int) -> None:
        """Update statistics after reception."""
        self._stats.bytes_received += byte_count

    def _update_stats_error(self) -> None:
        """Update statistics after error."""
        self._stats.errors += 1

    def _update_stats_retry(self) -> None:
        """Update statistics after retry."""
        self._stats.retries += 1

    def _update_stats_pec_failure(self) -> None:
        """Update statistics after PEC failure."""
        self._stats.pec_failures += 1


class TransportFactory:
    """Factory for creating transport instances."""

    _registry: dict[str, type[Transport]] = {}

    @classmethod
    def register(cls, name: str, transport_class: type[Transport]) -> None:
        """Register a transport implementation.

        Args:
            name: Transport name (e.g., "i2c", "uart")
            transport_class: Transport class to register
        """
        cls._registry[name.lower()] = transport_class

    @classmethod
    def create(cls, name: str, config: TransportConfig) -> Transport:
        """Create a transport instance.

        Args:
            name: Transport name (e.g., "i2c", "uart")
            config: Transport configuration

        Returns:
            Transport instance

        Raises:
            ValueError: If transport name is not registered
        """
        name_lower = name.lower()
        if name_lower not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(f"Unknown transport '{name}'. Available: {available}")
        return cls._registry[name_lower](config)

    @classmethod
    def available_transports(cls) -> list[str]:
        """Return list of available transport names."""
        return list(cls._registry.keys())
