"""
Unit tests for protocol enumerations.
"""

import pytest
from phoenix.protocol.enums import (
    BifurcationMode,
    MaxDataRate,
    ClockingMode,
    ResetType,
    LTSSMState,
    PRBSPattern,
    PCIeGeneration,
)


class TestBifurcationMode:
    """Tests for BifurcationMode enum."""

    def test_x16_mode(self):
        """Test X16 mode value."""
        assert BifurcationMode.X16.value == 0

    def test_x8_x8_mode(self):
        """Test X8_X8 mode value."""
        assert BifurcationMode.X8_X8.value == 3

    def test_total_lanes_x16(self):
        """Test total lanes calculation for X16."""
        assert BifurcationMode.X16.total_lanes == 16

    def test_total_lanes_x8_x8(self):
        """Test total lanes calculation for X8_X8."""
        assert BifurcationMode.X8_X8.total_lanes == 16

    def test_total_lanes_x4_x4_x4_x4(self):
        """Test total lanes calculation for X4_X4_X4_X4."""
        assert BifurcationMode.X4_X4_X4_X4.total_lanes == 16

    def test_all_modes_exist(self):
        """Test that all 33 bifurcation modes exist."""
        assert len(BifurcationMode) == 33


class TestMaxDataRate:
    """Tests for MaxDataRate enum."""

    def test_gen1_speed(self):
        """Test Gen1 speed."""
        assert MaxDataRate.GEN1_2P5G.speed_gt_s == 2.5

    def test_gen5_speed(self):
        """Test Gen5 speed."""
        assert MaxDataRate.GEN5_32G.speed_gt_s == 32.0

    def test_gen6_speed(self):
        """Test Gen6 speed."""
        assert MaxDataRate.GEN6_64G.speed_gt_s == 64.0

    def test_generation_number(self):
        """Test generation number extraction."""
        assert MaxDataRate.GEN3_8G.generation == 3
        assert MaxDataRate.GEN5_32G.generation == 5


class TestClockingMode:
    """Tests for ClockingMode enum."""

    def test_common_modes(self):
        """Test common clock modes exist."""
        assert ClockingMode.COMMON_WO_SSC.value == 0
        assert ClockingMode.COMMON_SSC.value == 1

    def test_sris_modes(self):
        """Test SRIS clock modes exist."""
        assert ClockingMode.SRIS_SSC.value == 4
        assert ClockingMode.SRIS_WO_SSC_LL.value == 7


class TestResetType:
    """Tests for ResetType enum."""

    def test_reset_types(self):
        """Test all reset types exist."""
        assert ResetType.HARD.value == 0
        assert ResetType.SOFT.value == 1
        assert ResetType.MAC.value == 2
        assert ResetType.PERST.value == 3
        assert ResetType.GLOBAL_SWRST.value == 4


class TestLTSSMState:
    """Tests for LTSSMState enum."""

    def test_detect_state(self):
        """Test DETECT state value."""
        assert LTSSMState.DETECT.value == 0x0

    def test_forwarding_state(self):
        """Test FWD_FORWARDING state value."""
        assert LTSSMState.FWD_FORWARDING.value == 0x4

    def test_execution_states(self):
        """Test execution states exist."""
        assert LTSSMState.EXE_CLB_ENTRY.value == 0x10
        assert LTSSMState.EXE_EQ_PH2_ACTIVE.value == 0x14


class TestPRBSPattern:
    """Tests for PRBSPattern enum."""

    def test_prbs_patterns(self):
        """Test PRBS pattern values."""
        assert PRBSPattern.PRBS7.value == 0
        assert PRBSPattern.PRBS31.value == 8
        assert PRBSPattern.PRBS58.value == 10

    def test_all_patterns_exist(self):
        """Test that all 11 PRBS patterns exist."""
        assert len(PRBSPattern) == 11
