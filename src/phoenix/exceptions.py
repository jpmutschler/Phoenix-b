"""
Phoenix exception hierarchy.

Maps to BCM_STATUS codes from the Broadcom Vantage SDK.
"""

from enum import IntEnum
from typing import Optional


class BCMStatus(IntEnum):
    """BCM library return status codes."""

    SUCCESS = 0x00000000
    FAILED = 0x00000001
    IGNORE = 0x00000002
    RETRY = 0x00000004
    UNSUPPORTED = 0x00000005
    LIBRARY_ALREADY_INITIALIZED = 0x00000006
    LIBRARY_VERSION_CONFLICT = 0x00000008
    INVALID_DEVICE_INDEX = 0x00000009
    OPERATION_RESTRICTED = 0x0000000A
    LIBRARY_NOT_INITIALIZED = 0x0000000B
    INVALID_FUNCTION = 0x0000000C
    NO_MEMORY = 0x00000010
    INSUFFICIENT_BUFFER = 0x00000011
    ILLEGAL_REQUEST = 0x00000012
    BUFFER_FULL = 0x00000014
    INVALID_STRUCT_VERSION = 0x00000015
    INVALID_PHY_IDENTIFIER = 0x00000016
    PRODUCT_TAMPERED = 0x00000017
    INVALID_PARAMETER = 0x00000018
    FILE_OPEN_FAILED = 0x00000019

    DISCOVERY_FAILURE = 0x00000020
    NO_MORE_ITEMS = 0x00000021
    UNKNOWN_DEVICE_TYPE = 0x00000022
    NON_BRCM_DEVICE = 0x00000023
    UNSUPPORTED_BRCM_DEVICE = 0x00000024
    FILTERED_DEVICE = 0x00000025

    INVALID_HANDLE = 0x00000030
    INVALID_ADDRESS = 0x00000031
    ADAPTER_OUT_OF_RANGE = 0x00000032
    HANDLE_VERSION_UNKNOWN = 0x00000033
    IOCTL_ERROR = 0x00000034
    ADAPTER_NOT_EXIST = 0x00000035
    ADAPTER_NOT_FOUND = 0x00000036
    ADAPTER_DISABLED = 0x00000037
    ADAPTER_INIT_FAILED = 0x00000038
    IOCTL_TIMEOUT = 0x0000003B
    INVALID_PORT = 0x0000003C

    # Firmware status codes
    FW_STAT_FAILED = 0x00000300
    FW_STAT_UNSUPPORTED = 0x00000301
    FW_STAT_NULL_PARAM = 0x00000302
    FW_STAT_INVALID_ADDR = 0x00000303
    FW_STAT_INVALID_DATA = 0x00000304
    FW_STAT_NO_RESOURCE = 0x00000305
    FW_STAT_TIMEOUT = 0x00000306
    FW_STAT_IN_USE = 0x00000307
    FW_STAT_DISABLED = 0x00000308
    FW_STAT_PENDING = 0x00000309
    FW_STAT_NOT_FOUND = 0x0000030A
    FW_STAT_INVALID_STATE = 0x0000030B
    FW_STAT_INVALID_PORT = 0x0000030C
    FW_STAT_INVALID_OBJECT = 0x0000030D
    FW_STAT_BUFFER_TOO_SMALL = 0x0000030E
    FW_STAT_INVALID_SIZE = 0x0000030F
    FW_STAT_RETRY = 0x00000310
    FW_STAT_ABORT = 0x00000311
    FW_STAT_INVALID_PARAM = 0x00000316

    # I2C/MCTP status codes
    I2C_WRITE_FAILED = 0x00000811
    I2C_READ_FAILED = 0x00000812
    MCTP_PEC_FAIL = 0x00000602
    MCTP_TIMEOUT = 0x00000706

    # CRC failure
    CODE_IMAGE_CRC_FAILURE = 0x30010425


class PhoenixError(Exception):
    """Base exception for all Phoenix API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[BCMStatus] = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message} (status: {self.status_code.name})"
        return self.message


class TransportError(PhoenixError):
    """Error in transport layer (I2C, UART, etc.)."""

    pass


class I2CError(TransportError):
    """I2C/SMBus communication error."""

    pass


class I2CWriteError(I2CError):
    """I2C write operation failed."""

    def __init__(self, address: int, data: bytes, message: str = "I2C write failed"):
        super().__init__(message, BCMStatus.I2C_WRITE_FAILED, {"address": address, "data": data})
        self.address = address
        self.data = data


class I2CReadError(I2CError):
    """I2C read operation failed."""

    def __init__(self, address: int, length: int, message: str = "I2C read failed"):
        super().__init__(message, BCMStatus.I2C_READ_FAILED, {"address": address, "length": length})
        self.address = address
        self.length = length


class PECMismatchError(I2CError):
    """Packet Error Checking (PEC) validation failed."""

    def __init__(self, expected: int, actual: int):
        super().__init__(
            f"PEC mismatch: expected 0x{expected:02X}, got 0x{actual:02X}",
            BCMStatus.MCTP_PEC_FAIL,
            {"expected": expected, "actual": actual},
        )
        self.expected = expected
        self.actual = actual


class UARTError(TransportError):
    """UART/Serial communication error."""

    pass


class DeviceNotFoundError(PhoenixError):
    """Requested device was not found."""

    def __init__(self, device_address: Optional[int] = None, message: str = "Device not found"):
        super().__init__(
            message, BCMStatus.ADAPTER_NOT_FOUND, {"device_address": device_address}
        )
        self.device_address = device_address


class InvalidParameterError(PhoenixError):
    """Invalid parameter provided to API."""

    def __init__(self, parameter: str, value: object, reason: str = ""):
        message = f"Invalid parameter '{parameter}': {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(
            message, BCMStatus.INVALID_PARAMETER, {"parameter": parameter, "value": value}
        )
        self.parameter = parameter
        self.value = value
        self.reason = reason


class InvalidAddressError(PhoenixError):
    """Invalid register address."""

    def __init__(self, address: int, message: str = "Invalid address"):
        super().__init__(message, BCMStatus.INVALID_ADDRESS, {"address": address})
        self.address = address


class InvalidPortError(PhoenixError):
    """Invalid port number specified."""

    def __init__(self, port: int, max_ports: int = 2):
        super().__init__(
            f"Invalid port {port}, valid range is 0-{max_ports - 1}",
            BCMStatus.INVALID_PORT,
            {"port": port, "max_ports": max_ports},
        )
        self.port = port
        self.max_ports = max_ports


class FirmwareError(PhoenixError):
    """Firmware-related error."""

    pass


class FirmwareDownloadError(FirmwareError):
    """Firmware download failed."""

    def __init__(self, message: str, stage: str = "unknown"):
        super().__init__(message, BCMStatus.FW_STAT_FAILED, {"stage": stage})
        self.stage = stage


class FirmwareCRCError(FirmwareError):
    """Firmware CRC validation failed."""

    def __init__(self, expected: int, actual: int):
        super().__init__(
            f"Firmware CRC mismatch: expected 0x{expected:08X}, got 0x{actual:08X}",
            BCMStatus.CODE_IMAGE_CRC_FAILURE,
            {"expected": expected, "actual": actual},
        )
        self.expected = expected
        self.actual = actual


class FirmwareStateError(FirmwareError):
    """Device is in wrong state for firmware operation."""

    def __init__(self, current_state: str, required_state: str):
        super().__init__(
            f"Device in '{current_state}' state, requires '{required_state}'",
            BCMStatus.FW_STAT_INVALID_STATE,
            {"current_state": current_state, "required_state": required_state},
        )
        self.current_state = current_state
        self.required_state = required_state


class TimeoutError(PhoenixError):
    """Operation timed out."""

    def __init__(self, operation: str, timeout_ms: int):
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_ms}ms",
            BCMStatus.FW_STAT_TIMEOUT,
            {"operation": operation, "timeout_ms": timeout_ms},
        )
        self.operation = operation
        self.timeout_ms = timeout_ms


class DeviceBusyError(PhoenixError):
    """Device is busy and cannot accept commands."""

    def __init__(self, message: str = "Device is busy"):
        super().__init__(message, BCMStatus.FW_STAT_IN_USE)


class UnsupportedOperationError(PhoenixError):
    """Requested operation is not supported."""

    def __init__(self, operation: str, reason: str = ""):
        message = f"Operation '{operation}' is not supported"
        if reason:
            message += f": {reason}"
        super().__init__(message, BCMStatus.UNSUPPORTED, {"operation": operation})
        self.operation = operation


class DiscoveryError(PhoenixError):
    """Device discovery failed."""

    def __init__(self, message: str, adapter_type: str = ""):
        super().__init__(
            message, BCMStatus.DISCOVERY_FAILURE, {"adapter_type": adapter_type}
        )
        self.adapter_type = adapter_type


class AdapterNotFoundError(PhoenixError):
    """USB adapter (Aardvark, FTDI) not found."""

    def __init__(self, adapter_type: str):
        super().__init__(
            f"{adapter_type} adapter not found",
            BCMStatus.ADAPTER_NOT_FOUND,
            {"adapter_type": adapter_type},
        )
        self.adapter_type = adapter_type


class AdapterInitError(PhoenixError):
    """USB adapter initialization failed."""

    def __init__(self, adapter_type: str, reason: str = ""):
        message = f"Failed to initialize {adapter_type} adapter"
        if reason:
            message += f": {reason}"
        super().__init__(message, BCMStatus.ADAPTER_INIT_FAILED, {"adapter_type": adapter_type})
        self.adapter_type = adapter_type


class ConfigurationError(PhoenixError):
    """Configuration operation failed."""

    def __init__(self, config_type: str, message: str):
        super().__init__(
            f"Configuration error for '{config_type}': {message}",
            details={"config_type": config_type},
        )
        self.config_type = config_type


class DiagnosticError(PhoenixError):
    """Diagnostic operation failed."""

    def __init__(self, diagnostic_type: str, message: str):
        super().__init__(
            f"Diagnostic '{diagnostic_type}' failed: {message}",
            details={"diagnostic_type": diagnostic_type},
        )
        self.diagnostic_type = diagnostic_type


def status_to_exception(status: int, context: str = "") -> PhoenixError:
    """Convert a BCM status code to an appropriate exception.

    Args:
        status: BCM_STATUS code from device
        context: Additional context for error message

    Returns:
        Appropriate PhoenixError subclass instance
    """
    try:
        bcm_status = BCMStatus(status)
    except ValueError:
        return PhoenixError(f"Unknown error: 0x{status:08X}", details={"context": context})

    message = f"{bcm_status.name}"
    if context:
        message = f"{context}: {message}"

    # Map status codes to specific exceptions
    status_exception_map = {
        BCMStatus.INVALID_PARAMETER: InvalidParameterError("unknown", status, message),
        BCMStatus.INVALID_ADDRESS: InvalidAddressError(0, message),
        BCMStatus.INVALID_PORT: InvalidPortError(0),
        BCMStatus.ADAPTER_NOT_FOUND: DeviceNotFoundError(message=message),
        BCMStatus.DISCOVERY_FAILURE: DiscoveryError(message),
        BCMStatus.I2C_WRITE_FAILED: I2CWriteError(0, b"", message),
        BCMStatus.I2C_READ_FAILED: I2CReadError(0, 0, message),
        BCMStatus.MCTP_PEC_FAIL: PECMismatchError(0, 0),
        BCMStatus.FW_STAT_TIMEOUT: TimeoutError("unknown", 0),
        BCMStatus.MCTP_TIMEOUT: TimeoutError("unknown", 0),
        BCMStatus.FW_STAT_IN_USE: DeviceBusyError(message),
        BCMStatus.UNSUPPORTED: UnsupportedOperationError("unknown", message),
        BCMStatus.CODE_IMAGE_CRC_FAILURE: FirmwareCRCError(0, 0),
    }

    if bcm_status in status_exception_map:
        return status_exception_map[bcm_status]

    # Default to base exception with status code
    return PhoenixError(message, bcm_status)
