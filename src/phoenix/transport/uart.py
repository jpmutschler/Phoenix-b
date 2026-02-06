"""
UART/Serial transport implementation for Broadcom Vantage retimer.

Provides communication with the retimer via the on-board MCU's serial debug interface.
"""

import asyncio
import struct
from typing import Optional

import serial
from serial import Serial

from phoenix.exceptions import (
    TimeoutError,
    TransportError,
    UARTError,
)
from phoenix.protocol.enums import RegisterAccessType
from phoenix.transport.base import (
    Transport,
    TransportFactory,
    TransportState,
    UARTConfig,
)
from phoenix.utils.logging import get_logger

logger = get_logger(__name__)


# UART protocol constants
UART_FRAME_START = 0xAA
UART_FRAME_END = 0x55
UART_CMD_READ_REG16 = 0x01
UART_CMD_WRITE_REG16 = 0x02
UART_CMD_READ_REG32 = 0x03
UART_CMD_WRITE_REG32 = 0x04
UART_CMD_READ_BLOCK = 0x05
UART_CMD_WRITE_BLOCK = 0x06
UART_CMD_STATUS = 0x07

UART_RESP_OK = 0x00
UART_RESP_ERROR = 0xFF


class UARTTransport(Transport):
    """UART/Serial transport implementation."""

    def __init__(self, config: UARTConfig):
        super().__init__(config)
        self._config: UARTConfig = config
        self._serial: Optional[Serial] = None
        self._lock = asyncio.Lock()

    @property
    def access_type(self) -> RegisterAccessType:
        return RegisterAccessType.UART

    async def connect(self) -> None:
        """Open serial port connection."""
        if self._state == TransportState.CONNECTED:
            return

        if not self._config.port:
            raise UARTError("Serial port not specified")

        self._state = TransportState.CONNECTING
        try:
            self._serial = Serial(
                port=self._config.port,
                baudrate=self._config.baud_rate,
                bytesize=self._config.data_bits,
                stopbits=self._config.stop_bits,
                parity=self._config.parity,
                timeout=self._config.timeout_ms / 1000.0,
                write_timeout=self._config.timeout_ms / 1000.0,
            )

            # Flush any pending data
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

            self._state = TransportState.CONNECTED
            logger.info(
                "uart_connected",
                port=self._config.port,
                baud_rate=self._config.baud_rate,
            )
        except serial.SerialException as e:
            self._state = TransportState.ERROR
            raise UARTError(f"Failed to open serial port: {e}") from e

    async def disconnect(self) -> None:
        """Close serial port connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self._state = TransportState.DISCONNECTED
        logger.info("uart_disconnected")

    async def read_register_16(self, address: int) -> int:
        """Read a 16-bit register via UART."""
        async with self._lock:
            return await self._do_read_16(address)

    async def write_register_16(self, address: int, value: int) -> None:
        """Write a 16-bit register via UART."""
        async with self._lock:
            await self._do_write_16(address, value)

    async def read_register_32(self, address: int) -> int:
        """Read a 32-bit register via UART."""
        async with self._lock:
            return await self._do_read_32(address)

    async def write_register_32(self, address: int, value: int) -> None:
        """Write a 32-bit register via UART."""
        async with self._lock:
            await self._do_write_32(address, value)

    async def read_block(self, address: int, length: int) -> bytes:
        """Read a block of data via UART."""
        async with self._lock:
            return await self._do_read_block(address, length)

    async def write_block(self, address: int, data: bytes) -> None:
        """Write a block of data via UART."""
        async with self._lock:
            await self._do_write_block(address, data)

    def _build_frame(self, cmd: int, data: bytes) -> bytes:
        """Build a UART frame with start/end markers and checksum.

        Frame format:
            START (1) | CMD (1) | LENGTH (2) | DATA (N) | CHECKSUM (1) | END (1)
        """
        length = len(data)
        frame = bytes([UART_FRAME_START, cmd]) + struct.pack("<H", length) + data
        checksum = sum(frame[1:]) & 0xFF  # Exclude START from checksum
        frame += bytes([checksum, UART_FRAME_END])
        return frame

    def _parse_response(self, response: bytes) -> tuple[int, bytes]:
        """Parse a UART response frame.

        Returns:
            Tuple of (status_code, data)
        """
        if len(response) < 6:
            raise UARTError(f"Response too short: {len(response)} bytes")

        if response[0] != UART_FRAME_START:
            raise UARTError(f"Invalid start byte: 0x{response[0]:02X}")

        if response[-1] != UART_FRAME_END:
            raise UARTError(f"Invalid end byte: 0x{response[-1]:02X}")

        status = response[1]
        length = struct.unpack("<H", response[2:4])[0]
        data = response[4 : 4 + length]

        # Verify checksum
        checksum = response[4 + length]
        expected = sum(response[1 : 4 + length]) & 0xFF
        if checksum != expected:
            raise UARTError(f"Checksum mismatch: expected 0x{expected:02X}, got 0x{checksum:02X}")

        return status, data

    async def _send_receive(self, cmd: int, data: bytes, expected_len: int) -> bytes:
        """Send command and receive response."""
        if not self._serial or not self._serial.is_open:
            raise UARTError("Serial port not open")

        frame = self._build_frame(cmd, data)
        self._update_stats_tx(len(frame))

        for attempt in range(self._config.retry_count):
            try:
                # Send frame
                self._serial.write(frame)
                self._serial.flush()

                # Read response header (START + STATUS + LENGTH)
                header = self._serial.read(4)
                if len(header) < 4:
                    raise TimeoutError("UART read header", self._config.timeout_ms)

                if header[0] != UART_FRAME_START:
                    raise UARTError(f"Invalid response start: 0x{header[0]:02X}")

                length = struct.unpack("<H", header[2:4])[0]

                # Read rest of response (DATA + CHECKSUM + END)
                rest = self._serial.read(length + 2)
                if len(rest) < length + 2:
                    raise TimeoutError("UART read data", self._config.timeout_ms)

                response = header + rest
                self._update_stats_rx(len(response))

                status, resp_data = self._parse_response(response)

                if status != UART_RESP_OK:
                    raise UARTError(f"Command failed with status: 0x{status:02X}")

                return resp_data

            except (TimeoutError, UARTError) as e:
                self._update_stats_error()
                if attempt < self._config.retry_count - 1:
                    self._update_stats_retry()
                    # Flush and retry
                    self._serial.reset_input_buffer()
                    await asyncio.sleep(0.01)
                    continue
                raise

        raise UARTError("Max retries exceeded")

    async def _do_read_16(self, address: int) -> int:
        """Internal 16-bit read implementation."""
        # Data: address (2 bytes, little-endian)
        data = struct.pack("<H", address)
        response = await self._send_receive(UART_CMD_READ_REG16, data, 2)

        if len(response) < 2:
            raise UARTError(f"Invalid response length: {len(response)}")

        return struct.unpack("<H", response[:2])[0]

    async def _do_write_16(self, address: int, value: int) -> None:
        """Internal 16-bit write implementation."""
        # Data: address (2 bytes) + value (2 bytes)
        data = struct.pack("<HH", address, value)
        await self._send_receive(UART_CMD_WRITE_REG16, data, 0)

    async def _do_read_32(self, address: int) -> int:
        """Internal 32-bit read implementation."""
        # Data: address (4 bytes for 32-bit address support)
        data = struct.pack("<I", address)
        response = await self._send_receive(UART_CMD_READ_REG32, data, 4)

        if len(response) < 4:
            raise UARTError(f"Invalid response length: {len(response)}")

        return struct.unpack("<I", response[:4])[0]

    async def _do_write_32(self, address: int, value: int) -> None:
        """Internal 32-bit write implementation."""
        # Data: address (4 bytes) + value (4 bytes)
        data = struct.pack("<II", address, value)
        await self._send_receive(UART_CMD_WRITE_REG32, data, 0)

    async def _do_read_block(self, address: int, length: int) -> bytes:
        """Internal block read implementation."""
        # Read in chunks to avoid buffer overflow
        result = bytearray()
        offset = address
        remaining = length
        chunk_size = 64  # Safe chunk size for UART

        while remaining > 0:
            read_len = min(remaining, chunk_size)
            # Data: address (4 bytes) + length (2 bytes)
            data = struct.pack("<IH", offset, read_len)
            response = await self._send_receive(UART_CMD_READ_BLOCK, data, read_len)
            result.extend(response)
            offset += read_len
            remaining -= read_len

        return bytes(result)

    async def _do_write_block(self, address: int, data: bytes) -> None:
        """Internal block write implementation."""
        # Write in chunks
        offset = address
        remaining = len(data)
        data_offset = 0
        chunk_size = 56  # Leave room for address in 64-byte chunks

        while remaining > 0:
            write_len = min(remaining, chunk_size)
            chunk = data[data_offset : data_offset + write_len]
            # Data: address (4 bytes) + data
            req_data = struct.pack("<I", offset) + chunk
            await self._send_receive(UART_CMD_WRITE_BLOCK, req_data, 0)
            offset += write_len
            remaining -= write_len
            data_offset += write_len


# Register transport with factory
TransportFactory.register("uart", UARTTransport)
