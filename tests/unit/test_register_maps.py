"""Unit tests for register map definitions."""

import pytest
from phoenix.protocol.register_maps import (
    RegisterField,
    Register,
    RegisterAccess,
)
from phoenix.protocol.chip_profile import load_profile


class TestRegisterField:
    """Tests for RegisterField class."""

    def test_mask_single_bit(self):
        """Test mask for single bit field."""
        field = RegisterField("TEST", bit_offset=5, bit_width=1)
        assert field.mask == 0x20  # 1 << 5

    def test_mask_multi_bit(self):
        """Test mask for multi-bit field."""
        field = RegisterField("TEST", bit_offset=4, bit_width=4)
        assert field.mask == 0xF0  # 0xF << 4

    def test_extract_value(self):
        """Test field value extraction."""
        field = RegisterField("TEST", bit_offset=8, bit_width=8)
        value = field.extract(0x12345678)
        assert value == 0x56

    def test_insert_value(self):
        """Test field value insertion."""
        field = RegisterField("TEST", bit_offset=8, bit_width=8)
        result = field.insert(0x12340078, 0xAB)
        assert result == 0x1234AB78

    def test_insert_preserves_other_bits(self):
        """Test that insert preserves bits outside field."""
        field = RegisterField("TEST", bit_offset=4, bit_width=4)
        result = field.insert(0xFF, 0x5)
        assert result == 0x5F  # Upper nibble and lower nibble preserved

    def test_extract_at_boundary(self):
        """Test extraction at bit 0."""
        field = RegisterField("TEST", bit_offset=0, bit_width=4)
        value = field.extract(0xABCDEF12)
        assert value == 0x2

    def test_extract_high_bits(self):
        """Test extraction of high bits."""
        field = RegisterField("TEST", bit_offset=28, bit_width=4)
        value = field.extract(0xABCDEF12)
        assert value == 0xA


class TestRegister:
    """Tests for Register class."""

    def test_register_basic(self):
        """Test basic register creation."""
        reg = Register(name="TEST_REG", address=0x1234)
        assert reg.name == "TEST_REG"
        assert reg.address == 0x1234
        assert reg.size == 4

    def test_get_field_exists(self):
        """Test getting existing field."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        field = global_param0.get_field("BIFURCATION")
        assert field is not None
        assert field.name == "BIFURCATION"

    def test_get_field_not_exists(self):
        """Test getting non-existent field."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        field = global_param0.get_field("NONEXISTENT")
        assert field is None


class TestGlobalParam0:
    """Tests for GLOBAL_PARAM0 register."""

    def test_address(self):
        """Test GLOBAL_PARAM0 address."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        assert global_param0.address == 0x0000

    def test_has_bifurcation_field(self):
        """Test BIFURCATION field exists."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        field = global_param0.get_field("BIFURCATION")
        assert field is not None
        assert field.bit_offset == 7
        assert field.bit_width == 6

    def test_has_max_data_rate_field(self):
        """Test MAX_DATA_RATE field exists."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        field = global_param0.get_field("MAX_DATA_RATE")
        assert field is not None
        assert field.bit_offset == 24
        assert field.bit_width == 3

    def test_extract_bifurcation(self):
        """Test extracting bifurcation mode from register value."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        # Value with bifurcation = 3 (X8_X8): bits [12:7] = 0b000011
        reg_value = 0x00000180  # 3 << 7
        field = global_param0.get_field("BIFURCATION")
        assert field.extract(reg_value) == 3


class TestGlobalParam1:
    """Tests for GLOBAL_PARAM1 register."""

    def test_address(self):
        """Test GLOBAL_PARAM1 address."""
        profile = load_profile()
        global_param1 = profile.get_register("GLOBAL_PARAM1")
        assert global_param1.address == 0x0004

    def test_vendor_id_field(self):
        """Test VENDOR_ID field."""
        profile = load_profile()
        global_param1 = profile.get_register("GLOBAL_PARAM1")
        field = global_param1.get_field("VENDOR_ID")
        assert field is not None
        assert field.bit_offset == 16
        assert field.bit_width == 16

    def test_extract_vendor_id(self):
        """Test extracting vendor ID."""
        profile = load_profile()
        global_param1 = profile.get_register("GLOBAL_PARAM1")
        # Broadcom vendor ID in bits [31:16]
        reg_value = 0x14E40000
        field = global_param1.get_field("VENDOR_ID")
        assert field.extract(reg_value) == 0x14E4


class TestRegisterAccess:
    """Tests for RegisterAccess helper class."""

    def test_get_field_value(self):
        """Test get_field_value helper."""
        profile = load_profile()
        global_param1 = profile.get_register("GLOBAL_PARAM1")
        reg_value = 0x14E467A0  # Typical GLOBAL_PARAM1 value
        vendor_id = RegisterAccess.get_field_value(global_param1, reg_value, "VENDOR_ID")
        assert vendor_id == 0x14E4

    def test_get_field_value_invalid(self):
        """Test get_field_value with invalid field."""
        profile = load_profile()
        global_param1 = profile.get_register("GLOBAL_PARAM1")
        with pytest.raises(ValueError):
            RegisterAccess.get_field_value(global_param1, 0, "INVALID_FIELD")

    def test_set_field_value(self):
        """Test set_field_value helper."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        reg_value = 0x00000000
        new_value = RegisterAccess.set_field_value(
            global_param0, reg_value, "BIFURCATION", 3
        )
        # Bifurcation 3 should be at bits [12:7]
        assert (new_value >> 7) & 0x3F == 3

    def test_set_field_value_invalid(self):
        """Test set_field_value with invalid field."""
        profile = load_profile()
        global_param0 = profile.get_register("GLOBAL_PARAM0")
        with pytest.raises(ValueError):
            RegisterAccess.set_field_value(global_param0, 0, "INVALID_FIELD", 0)


class TestAddressCalculations:
    """Tests for address calculation functions via profile."""

    def test_tx_coeff_address_gen3_lane0(self):
        """Test TX coefficient address for Gen3, Lane 0."""
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=3, lane=0)
        assert addr == 0x0200

    def test_tx_coeff_address_gen5_lane8(self):
        """Test TX coefficient address for Gen5, Lane 8."""
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=5, lane=8)
        # Gen5 base (0x0300) + lane 8 * 16
        assert addr == 0x0300 + (8 * 0x10)

    def test_tx_coeff_address_gen6(self):
        """Test TX coefficient address for Gen6."""
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=6, lane=0)
        assert addr == 0x0380


class TestRegistersDict:
    """Tests for registers dictionary from profile."""

    def test_registers_dict_populated(self):
        """Test that registers dict is populated."""
        profile = load_profile()
        assert len(profile.registers) > 0

    def test_can_lookup_registers(self):
        """Test looking up registers by name."""
        profile = load_profile()
        assert "GLOBAL_PARAM0" in profile.registers
        assert "GLOBAL_PARAM1" in profile.registers
        assert "TEMPERATURE" in profile.registers

    def test_register_values_are_registers(self):
        """Test that dict values are Register instances."""
        profile = load_profile()
        for name, reg in profile.registers.items():
            assert isinstance(reg, Register)
            assert reg.name != ""
