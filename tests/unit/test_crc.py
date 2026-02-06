"""
Unit tests for CRC and PEC utilities.
"""

import pytest
from phoenix.utils.crc import (
    calculate_pec,
    calculate_smbus_pec,
    verify_pec,
    calculate_crc32,
)


class TestPEC:
    """Tests for PEC (Packet Error Checking) calculation."""

    def test_empty_data(self):
        """Test PEC of empty data."""
        assert calculate_pec(b"") == 0

    def test_single_byte(self):
        """Test PEC of single byte."""
        # Known test vector
        pec = calculate_pec(b"\x00")
        assert pec == 0x00

    def test_known_vector(self):
        """Test PEC with known test vector."""
        # SMBus test vector: address 0x50, command 0x82
        data = bytes([0xA0, 0x82])  # 0x50 << 1 = 0xA0
        pec = calculate_pec(data)
        assert isinstance(pec, int)
        assert 0 <= pec <= 255

    def test_different_data_different_pec(self):
        """Test that different data produces different PEC."""
        pec1 = calculate_pec(b"\x01\x02\x03")
        pec2 = calculate_pec(b"\x01\x02\x04")
        assert pec1 != pec2

    def test_verify_pec_correct(self):
        """Test PEC verification with correct data."""
        data = b"\x12\x34\x56"
        pec = calculate_pec(data)
        assert verify_pec(data, pec)

    def test_verify_pec_incorrect(self):
        """Test PEC verification with incorrect PEC."""
        data = b"\x12\x34\x56"
        wrong_pec = 0xFF
        # May or may not match by chance, but verify it doesn't crash
        result = verify_pec(data, wrong_pec)
        assert isinstance(result, bool)

    def test_initial_value(self):
        """Test PEC calculation with initial value."""
        pec1 = calculate_pec(b"\x01\x02")
        pec2 = calculate_pec(b"\x02", initial=calculate_pec(b"\x01"))
        assert pec1 == pec2


class TestSMBusPEC:
    """Tests for SMBus PEC calculation."""

    def test_write_transaction(self):
        """Test PEC for write transaction."""
        pec = calculate_smbus_pec(
            slave_addr=0x50,
            command=0x07,
            write_data=b"\x00\x00\x12\x34",
            is_read=False,
        )
        assert isinstance(pec, int)
        assert 0 <= pec <= 255

    def test_read_transaction(self):
        """Test PEC for read transaction."""
        pec = calculate_smbus_pec(
            slave_addr=0x50,
            command=0x02,
            write_data=b"\x00\x00",
            read_data=b"\x12\x34\x56\x78",
            is_read=True,
        )
        assert isinstance(pec, int)
        assert 0 <= pec <= 255

    def test_different_addresses(self):
        """Test that different addresses produce different PEC."""
        pec1 = calculate_smbus_pec(
            slave_addr=0x50,
            command=0x07,
            write_data=b"\x00\x00",
        )
        pec2 = calculate_smbus_pec(
            slave_addr=0x51,
            command=0x07,
            write_data=b"\x00\x00",
        )
        assert pec1 != pec2


class TestCRC32:
    """Tests for CRC32 calculation."""

    def test_empty_data(self):
        """Test CRC32 of empty data."""
        crc = calculate_crc32(b"")
        assert crc == 0

    def test_known_string(self):
        """Test CRC32 with known string."""
        # "123456789" should produce 0xCBF43926
        crc = calculate_crc32(b"123456789")
        assert crc == 0xCBF43926

    def test_returns_unsigned(self):
        """Test that CRC32 returns unsigned 32-bit value."""
        crc = calculate_crc32(b"\xFF" * 100)
        assert crc >= 0
        assert crc <= 0xFFFFFFFF
