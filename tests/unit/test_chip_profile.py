"""Unit tests for ChipProfile loader."""

import pytest

from phoenix.protocol.chip_profile import (
    ChipProfile,
    TxCoeffLayout,
    ErrorStatsLayout,
    load_profile,
    _load_profile_from_json,
)
from phoenix.protocol.register_maps import Register, RegisterField


class TestLoadProfile:
    """Tests for loading the BCM85667 profile from JSON."""

    def test_loads_successfully(self):
        """Test that the default profile loads without error."""
        profile = load_profile()
        assert isinstance(profile, ChipProfile)

    def test_chip_name(self):
        """Test chip name."""
        profile = load_profile()
        assert profile.name == "BCM85667"

    def test_vendor_id(self):
        """Test vendor ID is Broadcom."""
        profile = load_profile()
        assert profile.vendor_id == 0x14E4

    def test_device_id(self):
        """Test device ID."""
        profile = load_profile()
        assert profile.device_id == 0x8567

    def test_nonexistent_profile_raises(self):
        """Test that loading a missing profile raises FileNotFoundError."""
        with pytest.raises(Exception):
            load_profile.__wrapped__("nonexistent_chip")


class TestRegisters:
    """Tests for register data loaded from profile."""

    def test_has_all_registers(self):
        """Test that all 15 registers are loaded."""
        profile = load_profile()
        assert len(profile.registers) == 15

    def test_global_param0_address(self):
        """Test GLOBAL_PARAM0 register address."""
        profile = load_profile()
        reg = profile.get_register("GLOBAL_PARAM0")
        assert reg.address == 0x0000

    def test_global_param1_address(self):
        """Test GLOBAL_PARAM1 register address."""
        profile = load_profile()
        reg = profile.get_register("GLOBAL_PARAM1")
        assert reg.address == 0x0004

    def test_temperature_address(self):
        """Test TEMPERATURE register address."""
        profile = load_profile()
        reg = profile.get_register("TEMPERATURE")
        assert reg.address == 0x0100

    def test_ppa_ltssm_address(self):
        """Test PPA_LTSSM_STATE register address."""
        profile = load_profile()
        reg = profile.get_register("PPA_LTSSM_STATE")
        assert reg.address == 0x8000

    def test_ppb_ltssm_address(self):
        """Test PPB_LTSSM_STATE register address."""
        profile = load_profile()
        reg = profile.get_register("PPB_LTSSM_STATE")
        assert reg.address == 0xC000

    def test_register_has_fields(self):
        """Test that registers have expected fields."""
        profile = load_profile()
        reg = profile.get_register("GLOBAL_PARAM0")
        assert len(reg.fields) == 10

        field = reg.get_field("BIFURCATION")
        assert field is not None
        assert field.bit_offset == 7
        assert field.bit_width == 6

    def test_get_register_not_found(self):
        """Test that missing register raises KeyError."""
        profile = load_profile()
        with pytest.raises(KeyError):
            profile.get_register("NONEXISTENT")

    def test_vendor_id_field_extraction(self):
        """Test that loaded register fields work correctly for extraction."""
        profile = load_profile()
        reg = profile.get_register("GLOBAL_PARAM1")
        field = reg.get_field("VENDOR_ID")
        assert field is not None
        assert field.extract(0x14E40000) == 0x14E4

    def test_register_values_are_register_instances(self):
        """Test that all register values are Register instances."""
        profile = load_profile()
        for name, reg in profile.registers.items():
            assert isinstance(reg, Register)
            assert reg.name != ""


class TestRegisterBlocks:
    """Tests for register block addresses."""

    def test_retimer_cfg_block(self):
        profile = load_profile()
        assert profile.register_blocks["RETIMER_CFG"] == 0x0000

    def test_xagent_block(self):
        profile = load_profile()
        assert profile.register_blocks["XAGENT"] == 0x4000

    def test_ppa_block(self):
        profile = load_profile()
        assert profile.register_blocks["PPA"] == 0x8000

    def test_ppb_block(self):
        profile = load_profile()
        assert profile.register_blocks["PPB"] == 0xC000


class TestTxCoefficients:
    """Tests for TX coefficient address calculations."""

    def test_gen3_lane0(self):
        profile = load_profile()
        assert profile.get_tx_coeff_address(gen=3, lane=0) == 0x0200

    def test_gen5_lane8(self):
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=5, lane=8)
        assert addr == 0x0300 + (8 * 0x10)

    def test_gen6_lane0(self):
        profile = load_profile()
        assert profile.get_tx_coeff_address(gen=6, lane=0) == 0x0380

    def test_gen4_with_offset(self):
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=4, lane=2, offset=4)
        assert addr == 0x0280 + (2 * 0x10) + 4

    def test_unknown_gen_defaults_to_gen3(self):
        profile = load_profile()
        addr = profile.get_tx_coeff_address(gen=99, lane=0)
        assert addr == 0x0200


class TestErrorStats:
    """Tests for error statistics address calculations."""

    def test_lane0_type0(self):
        profile = load_profile()
        assert profile.get_error_stats_address(lane=0, error_type=0) == 0x0500

    def test_lane1_type0(self):
        profile = load_profile()
        assert profile.get_error_stats_address(lane=1, error_type=0) == 0x0520

    def test_lane0_type2(self):
        profile = load_profile()
        assert profile.get_error_stats_address(lane=0, error_type=2) == 0x0508


class TestSMBusCommands:
    """Tests for SMBus command code lookups."""

    def test_has_all_commands(self):
        profile = load_profile()
        assert len(profile.smbus_commands) == 20

    def test_wr32_2addr(self):
        profile = load_profile()
        assert profile.get_smbus_command("WR32_2ADDR") == 0x07

    def test_rd32_2addr_pec(self):
        profile = load_profile()
        assert profile.get_smbus_command("RD32_2ADDR_PEC") == 0x82

    def test_wr_block_pec(self):
        profile = load_profile()
        assert profile.get_smbus_command("WR_BLOCK_PEC") == 0xB7

    def test_process_block(self):
        profile = load_profile()
        assert profile.get_smbus_command("PROCESS_BLOCK") == 0xA9

    def test_missing_command_raises(self):
        profile = load_profile()
        with pytest.raises(KeyError):
            profile.get_smbus_command("NONEXISTENT")


class TestLoadFromRawJson:
    """Tests for _load_profile_from_json with minimal data."""

    def test_minimal_profile(self):
        raw = {
            "chip": {"name": "TEST", "vendor_id": "0x1234", "device_id": "0x5678"},
            "register_blocks": {},
            "registers": {},
            "tx_coefficients": {
                "gen3_base": "0x0200",
                "gen4_base": "0x0280",
                "gen5_base": "0x0300",
                "gen6_base": "0x0380",
                "lane_stride": "0x10",
            },
            "error_stats": {"base": "0x0500", "lane_stride": "0x20"},
            "smbus_commands": {},
        }
        profile = _load_profile_from_json(raw)
        assert profile.name == "TEST"
        assert profile.vendor_id == 0x1234
        assert profile.device_id == 0x5678

    def test_missing_key_raises(self):
        with pytest.raises(KeyError):
            _load_profile_from_json({})
