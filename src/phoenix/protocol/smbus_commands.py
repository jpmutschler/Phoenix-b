"""SMBus command encoding and decoding for retimer register access.

Implements the Intel SMBus protocol used by the retimer for register access
and firmware operations. Command codes are loaded from the chip profile.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from phoenix.utils.crc import calculate_smbus_pec


def _default_commands() -> dict[str, int]:
    """Lazily load the default SMBus command codes from the chip profile."""
    from phoenix.protocol.chip_profile import load_profile

    return load_profile().smbus_commands


@dataclass
class SMBusCommand:
    """SMBus command structure for register operations."""

    command_code: int
    command_name: str
    address: int
    data: bytes = b""
    use_pec: bool = True

    @property
    def is_read(self) -> bool:
        """Check if this is a read command."""
        return self.command_name.startswith("RD")

    @property
    def address_bytes(self) -> int:
        """Return number of address bytes (2 or 4)."""
        if "4ADDR" in self.command_name:
            return 4
        return 2


def _cmd(name: str, commands: Optional[dict[str, int]] = None) -> int:
    """Look up a command code by name, falling back to default profile."""
    cmds = commands if commands is not None else _default_commands()
    return cmds[name]


def encode_write_register_16(
    address: int,
    value: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a 16-bit register write command.

    Args:
        address: 16-bit register address
        value: 16-bit value to write
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, data_bytes)
    """
    cmd = _cmd("WR32_2ADDR_PEC", commands) if use_pec else _cmd("WR32_2ADDR", commands)

    data = bytes([
        (address >> 8) & 0xFF,
        address & 0xFF,
        value & 0xFF,
        (value >> 8) & 0xFF,
    ])

    return cmd, data


def encode_write_register_32(
    address: int,
    value: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a 32-bit register write command.

    For 32-bit addresses:
        Uses 4-byte address format

    For 16-bit addresses:
        Uses 2-byte address format

    Args:
        address: Register address (16 or 32-bit)
        value: 32-bit value to write
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, data_bytes)
    """
    if address > 0xFFFF:
        cmd = _cmd("WR32_4ADDR_PEC", commands) if use_pec else _cmd("WR32_4ADDR", commands)
        data = bytes([
            (address >> 24) & 0xFF,
            (address >> 16) & 0xFF,
            (address >> 8) & 0xFF,
            address & 0xFF,
            value & 0xFF,
            (value >> 8) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 24) & 0xFF,
        ])
    else:
        cmd = _cmd("WR32_2ADDR_PEC", commands) if use_pec else _cmd("WR32_2ADDR", commands)
        data = bytes([
            (address >> 8) & 0xFF,
            address & 0xFF,
            value & 0xFF,
            (value >> 8) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 24) & 0xFF,
        ])

    return cmd, data


def encode_read_register_16(
    address: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a 16-bit register read command.

    Args:
        address: 16-bit register address
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, address_bytes)
    """
    cmd = _cmd("RD32_2ADDR_PEC", commands) if use_pec else _cmd("RD32_2ADDR", commands)

    data = bytes([
        (address >> 8) & 0xFF,
        address & 0xFF,
    ])

    return cmd, data


def encode_read_register_32(
    address: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a 32-bit register read command.

    Args:
        address: Register address (16 or 32-bit)
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, address_bytes)
    """
    if address > 0xFFFF:
        cmd = _cmd("RD32_4ADDR_PEC", commands) if use_pec else _cmd("RD32_4ADDR", commands)
        data = bytes([
            (address >> 24) & 0xFF,
            (address >> 16) & 0xFF,
            (address >> 8) & 0xFF,
            address & 0xFF,
        ])
    else:
        cmd = _cmd("RD32_2ADDR_PEC", commands) if use_pec else _cmd("RD32_2ADDR", commands)
        data = bytes([
            (address >> 8) & 0xFF,
            address & 0xFF,
        ])

    return cmd, data


def decode_read_response_16(data: bytes) -> int:
    """Decode a 16-bit register read response.

    Args:
        data: Response bytes (2 bytes for value, optional 1 byte for PEC)

    Returns:
        16-bit register value
    """
    if len(data) < 2:
        raise ValueError(f"Insufficient data for 16-bit read: {len(data)} bytes")
    return data[0] | (data[1] << 8)


def decode_read_response_32(data: bytes) -> int:
    """Decode a 32-bit register read response.

    Args:
        data: Response bytes (4 bytes for value, optional 1 byte for PEC)

    Returns:
        32-bit register value
    """
    if len(data) < 4:
        raise ValueError(f"Insufficient data for 32-bit read: {len(data)} bytes")
    return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)


def encode_block_write(
    command: int,
    data: bytes,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a block write command.

    Args:
        command: Block command code
        data: Data to write
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, data_with_length)
    """
    cmd = _cmd("WR_BLOCK_PEC", commands) if use_pec else _cmd("WR_BLOCK", commands)
    block_data = bytes([len(data)]) + data

    return cmd, block_data


def encode_process_call(
    write_data: bytes,
    expected_read_len: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a block process call command.

    This is a write-then-read operation in a single SMBus transaction.

    Args:
        write_data: Data to write
        expected_read_len: Expected read length
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, data_with_length)
    """
    cmd = (
        _cmd("PROCESS_BLOCK_PEC", commands) if use_pec else _cmd("PROCESS_BLOCK", commands)
    )
    block_data = bytes([len(write_data)]) + write_data

    return cmd, block_data


def encode_get_status(
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> int:
    """Encode a get status command.

    Args:
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Command code
    """
    return _cmd("GET_STATUS_PEC", commands) if use_pec else _cmd("GET_STATUS", commands)


def encode_long_block_read(
    offset: int,
    length: int,
    use_pec: bool = True,
    commands: Optional[dict[str, int]] = None,
) -> Tuple[int, bytes]:
    """Encode a long block read command.

    Used for reading large data blocks (e.g., firmware upload).

    Args:
        offset: Start offset
        length: Number of bytes to read
        use_pec: Enable PEC calculation
        commands: Optional SMBus command dict (defaults to profile)

    Returns:
        Tuple of (command_code, setup_data)
    """
    cmd = (
        _cmd("RD_LONG_BLOCK_PEC", commands) if use_pec else _cmd("RD_LONG_BLOCK", commands)
    )

    data = bytes([
        offset & 0xFF,
        (offset >> 8) & 0xFF,
        (offset >> 16) & 0xFF,
        (offset >> 24) & 0xFF,
        length & 0xFF,
        (length >> 8) & 0xFF,
    ])

    return cmd, data


def calculate_command_pec(
    slave_addr: int,
    command: int,
    write_data: bytes = b"",
    read_data: bytes = b"",
) -> int:
    """Calculate PEC for a complete SMBus command.

    Args:
        slave_addr: 7-bit I2C slave address
        command: SMBus command byte
        write_data: Data being written
        read_data: Data being read

    Returns:
        8-bit PEC value
    """
    is_read = bool(read_data)
    return calculate_smbus_pec(slave_addr, command, write_data, read_data, is_read)
