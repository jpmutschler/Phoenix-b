"""
Diagnostic data models for the Broadcom Vantage retimer.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from phoenix.protocol.enums import (
    PRBSPattern,
    MaxDataRate,
    ELAType,
    ELATriggerType,
    ELATriggerPosition,
    BELAStatus,
    BELAState,
    BELATriggerType,
    LinkCATMode,
)


class PRBSConfig(BaseModel):
    """PRBS generator/checker configuration."""

    pattern: PRBSPattern = Field(
        default=PRBSPattern.PRBS31, description="PRBS polynomial pattern"
    )
    data_rate: MaxDataRate = Field(
        default=MaxDataRate.GEN5_32G, description="Data rate for PRBS"
    )
    lanes: List[int] = Field(
        default_factory=list, description="Lanes to enable (0-15)"
    )
    generator_enable: bool = Field(default=True, description="Enable PRBS generator")
    checker_enable: bool = Field(default=True, description="Enable PRBS checker")
    sample_count: int = Field(
        default=0x100000, ge=0, description="Sample count for checker"
    )

    model_config = {"frozen": False}


class PRBSResult(BaseModel):
    """PRBS test results for a lane."""

    lane_number: int = Field(description="Lane number")
    bit_count: int = Field(default=0, description="Total bits checked")
    error_count: int = Field(default=0, description="Bit errors detected")
    sync_acquired: bool = Field(default=False, description="Checker sync acquired")
    test_complete: bool = Field(default=False, description="Test complete")

    @property
    def bit_error_rate(self) -> float:
        """Calculate bit error rate."""
        if self.bit_count == 0:
            return 0.0
        return self.error_count / self.bit_count

    @property
    def ber_string(self) -> str:
        """Return BER as formatted string."""
        ber = self.bit_error_rate
        if ber == 0:
            return "< 1e-15"
        return f"{ber:.2e}"

    model_config = {"frozen": False}


class EyeMargin(BaseModel):
    """Eye diagram margin values."""

    left_margin_mui: int = Field(default=0, description="Left eye margin in mUI")
    right_margin_mui: int = Field(default=0, description="Right eye margin in mUI")
    upper_margin_mv: int = Field(default=0, description="Upper eye margin in mV")
    lower_margin_mv: int = Field(default=0, description="Lower eye margin in mV")

    @property
    def horizontal_opening_mui(self) -> int:
        """Calculate horizontal eye opening in mUI."""
        return self.left_margin_mui + self.right_margin_mui

    @property
    def vertical_opening_mv(self) -> int:
        """Calculate vertical eye opening in mV."""
        return self.upper_margin_mv + self.lower_margin_mv

    model_config = {"frozen": False}


class EyeDiagramResult(BaseModel):
    """Eye diagram capture result for a lane."""

    lane_number: int = Field(description="Lane number")
    data_rate: MaxDataRate = Field(description="Data rate during capture")
    middle_eye: EyeMargin = Field(
        default_factory=EyeMargin, description="Middle eye margin"
    )
    lower_eye: Optional[EyeMargin] = Field(
        default=None, description="Lower eye margin (Gen6)"
    )
    upper_eye: Optional[EyeMargin] = Field(
        default=None, description="Upper eye margin (Gen6)"
    )
    capture_valid: bool = Field(default=False, description="Capture valid")

    model_config = {"frozen": False}


class ELASignalConfig(BaseModel):
    """ELA (Embedded Logic Analyzer) signal configuration."""

    valid: bool = Field(default=True, description="Configuration valid")
    ela_type: ELAType = Field(
        default=ELAType.PSEUDO_PORT_A, description="ELA block type"
    )
    type_value: int = Field(
        default=0, description="Lane or port number based on ela_type"
    )
    signal_select: int = Field(default=0, description="Signal to trigger on")
    signal_value: int = Field(default=0, description="Signal value to match")
    trigger_type: ELATriggerType = Field(
        default=ELATriggerType.RISING, description="Trigger type"
    )

    model_config = {"frozen": False}


class ELAConfig(BaseModel):
    """ELA configuration."""

    signals: List[ELASignalConfig] = Field(
        default_factory=list, max_length=8, description="Signal configurations (max 8)"
    )
    trigger_position: ELATriggerPosition = Field(
        default=ELATriggerPosition.POS_50, description="Trigger position"
    )
    mixed_mode: bool = Field(
        default=False, description="Mixed mode (multiple conditions)"
    )
    enable: bool = Field(default=False, description="Enable ELA")

    model_config = {"frozen": False}


class ELAResult(BaseModel):
    """ELA capture result."""

    triggered: bool = Field(default=False, description="Trigger occurred")
    sample_count: int = Field(default=0, description="Number of samples captured")
    capture_data: bytes = Field(default=b"", description="Captured data")

    model_config = {"frozen": False}


class BELAConfig(BaseModel):
    """BELA (Broadcom Embedded Logic Analyzer) configuration."""

    lanes: List[int] = Field(
        default_factory=list, max_length=1, description="Lanes to monitor (max 1)"
    )
    trigger_rate: MaxDataRate = Field(
        default=MaxDataRate.GEN5_32G, description="Trigger data rate"
    )
    trigger_type: BELATriggerType = Field(
        default=BELATriggerType.LIVE_DATARATE, description="Trigger type"
    )
    enable: bool = Field(default=False, description="Enable BELA")
    force_capture: bool = Field(default=False, description="Force capture")
    auto_restart: bool = Field(default=False, description="Auto restart capture")

    model_config = {"frozen": False}


class BELACaptureStatus(BaseModel):
    """BELA capture status."""

    status: BELAStatus = Field(
        default=BELAStatus.RESERVED, description="Current BELA status"
    )
    state: BELAState = Field(
        default=BELAState.INIT, description="Current state machine state"
    )
    sample_size: int = Field(default=0, description="Bytes per sample")
    buffer_full: bool = Field(default=False, description="Buffer full")
    time_since_trigger_us: int = Field(
        default=0, description="Time since trigger in microseconds"
    )
    auto_restart_count: int = Field(default=0, description="Auto restart counter")

    @property
    def is_triggered(self) -> bool:
        """Check if BELA has triggered."""
        return self.status == BELAStatus.TRIGGERED

    @property
    def is_busy(self) -> bool:
        """Check if BELA is busy."""
        return self.status == BELAStatus.BUSY

    model_config = {"frozen": False}


class LinkCATConfig(BaseModel):
    """LinkCAT (Link Channel Analysis Tool) configuration."""

    mode: LinkCATMode = Field(default=LinkCATMode.LP_TX, description="LinkCAT mode")
    amplitude_scale: int = Field(
        default=0, ge=0, le=99, description="TX amplitude scale (0 for default)"
    )
    output_dir: str = Field(default="", description="Output directory for results")
    file_prefix: str = Field(default="linkcat", description="Output file prefix")

    model_config = {"frozen": False}


class LinkCATResult(BaseModel):
    """LinkCAT analysis result."""

    insertion_loss_db: float = Field(
        default=-99.0, description="Insertion loss at symbol rate in dB"
    )
    fit_factor: float = Field(default=0.0, description="Calculation fit factor")
    clipped: bool = Field(default=False, description="Data was clipped")
    error_or_warning: bool = Field(
        default=False, description="Error or warning occurred"
    )

    @property
    def is_valid(self) -> bool:
        """Check if result is valid."""
        return self.insertion_loss_db > -99.0 and not self.error_or_warning

    model_config = {"frozen": False}


class DiagnosticSummary(BaseModel):
    """Summary of diagnostic results."""

    prbs_results: List[PRBSResult] = Field(
        default_factory=list, description="PRBS results per lane"
    )
    eye_results: List[EyeDiagramResult] = Field(
        default_factory=list, description="Eye diagram results per lane"
    )
    linkcat_result: Optional[LinkCATResult] = Field(
        default=None, description="LinkCAT result"
    )

    @property
    def all_lanes_pass_prbs(self) -> bool:
        """Check if all lanes passed PRBS test."""
        if not self.prbs_results:
            return False
        return all(r.error_count == 0 for r in self.prbs_results)

    model_config = {"frozen": False}
