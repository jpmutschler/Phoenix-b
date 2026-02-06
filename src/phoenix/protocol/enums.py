"""
Protocol enumerations for the Broadcom Vantage BCM85667 PCIe Gen6 Retimer.

Ported from bcmdef.h in the VNT6_0_0_2 SDK.
"""

from enum import IntEnum, auto


# Constants
PCIE_RETIMER_MAX_PORTS = 8
PCIE_RETIMER_MAX_LANES = 16
REGISTER_ACC_MAX = 32


class HandleType(IntEnum):
    """Handle types for device identification."""

    NONE = 0
    RETIMER_I2C = 0x10000001
    RETIMER_UART = 0x10000002
    RETIMER_MDIO = 0x10000003


class RegisterAccessType(IntEnum):
    """Register access type for read/write operations."""

    UNKNOWN = -1
    SMBUS = 0
    MDIO = 1
    UART = 2


class DiscoveryType(IntEnum):
    """Interface/communication type for discovery."""

    RESERVED1 = 1
    RESERVED2 = 2
    OOB_I2C = 3


class ProductFamily(IntEnum):
    """Product family types."""

    INVALID = 0
    PCIE_RETIMER = auto()


class BaudRate(IntEnum):
    """Baud rates for UART communication."""

    UNKNOWN = 0
    BAUD_110 = auto()
    BAUD_300 = auto()
    BAUD_600 = auto()
    BAUD_1200 = auto()
    BAUD_2400 = auto()
    BAUD_4800 = auto()
    BAUD_9600 = auto()
    BAUD_14400 = auto()
    BAUD_19200 = auto()
    BAUD_38400 = auto()
    BAUD_57600 = auto()
    BAUD_115200 = auto()
    BAUD_230400 = auto()

    def to_int(self) -> int:
        """Convert enum to actual baud rate integer."""
        rates = {
            BaudRate.BAUD_110: 110,
            BaudRate.BAUD_300: 300,
            BaudRate.BAUD_600: 600,
            BaudRate.BAUD_1200: 1200,
            BaudRate.BAUD_2400: 2400,
            BaudRate.BAUD_4800: 4800,
            BaudRate.BAUD_9600: 9600,
            BaudRate.BAUD_14400: 14400,
            BaudRate.BAUD_19200: 19200,
            BaudRate.BAUD_38400: 38400,
            BaudRate.BAUD_57600: 57600,
            BaudRate.BAUD_115200: 115200,
            BaudRate.BAUD_230400: 230400,
        }
        return rates.get(self, 0)


class RetimerMode(IntEnum):
    """Retimer operating mode."""

    UNKNOWN = 0
    BASE = auto()
    MCTP_RESERVED = auto()


class FirmwareLoadMethod(IntEnum):
    """Firmware download method."""

    INTERNAL = 0  # Download FW to internal memory
    TO_NVM = auto()  # Download FW to internal memory and NVM
    FROM_NVM = auto()  # Download FW from NVM


class SMBusBlockSize(IntEnum):
    """SMBus block size for firmware download."""

    BLOCK_32 = 0  # 32 bytes block size for SMBus 2.0
    BLOCK_64 = auto()  # 64 bytes block size for SMBus 3.0


class PortOrientation(IntEnum):
    """Port orientation configuration."""

    STATIC = 0  # PPA and PPB predefined
    DYNAMIC = auto()  # PPA and PPB defined dynamically


class SRISLinkPayloadSize(IntEnum):
    """SRIS link payload size."""

    SIZE_128 = 0
    SIZE_256 = auto()
    SIZE_512 = auto()
    SIZE_1024 = auto()


class MaxDataRate(IntEnum):
    """Maximum data rate (PCIe generation)."""

    RESERVED = 0
    GEN1_2P5G = auto()  # PCIe Gen1: 2.5 GT/s
    GEN2_5G = auto()  # PCIe Gen2: 5 GT/s
    GEN3_8G = auto()  # PCIe Gen3: 8 GT/s
    GEN4_16G = auto()  # PCIe Gen4: 16 GT/s
    GEN5_32G = auto()  # PCIe Gen5: 32 GT/s
    GEN6_64G = auto()  # PCIe Gen6: 64 GT/s

    @property
    def speed_gt_s(self) -> float:
        """Return speed in GT/s."""
        speeds = {
            MaxDataRate.GEN1_2P5G: 2.5,
            MaxDataRate.GEN2_5G: 5.0,
            MaxDataRate.GEN3_8G: 8.0,
            MaxDataRate.GEN4_16G: 16.0,
            MaxDataRate.GEN5_32G: 32.0,
            MaxDataRate.GEN6_64G: 64.0,
        }
        return speeds.get(self, 0.0)

    @property
    def generation(self) -> int:
        """Return PCIe generation number."""
        return self.value if self.value > 0 else 0


class ClockingMode(IntEnum):
    """Clocking mode configuration."""

    COMMON_WO_SSC = 0  # Common clock, no SSC
    COMMON_SSC = auto()  # Common clock with SSC
    SRNS_WO_SSC = auto()  # SRNS, no SSC
    RESERVED3 = auto()
    SRIS_SSC = auto()  # SRIS with SSC (no low latency)
    SRIS_WO_SSC = auto()  # SRIS, no SSC (debug only)
    RESERVED6 = auto()
    SRIS_WO_SSC_LL = auto()  # SRIS, no SSC (low latency)


class ResetType(IntEnum):
    """Reset type for device reset operations."""

    HARD = 0  # Hard reset - entire chip including all registers
    SOFT = auto()  # Soft reset - except sticky registers
    MAC = auto()  # Global MAC software reset
    PERST = auto()  # PERST fundamental reset
    GLOBAL_SWRST = auto()  # Toggle global software link reset


class BifurcationMode(IntEnum):
    """Bifurcation mode (link or MAC to lane subdivision)."""

    X16 = 0
    X8 = auto()
    X4 = auto()
    X8_X8 = auto()
    X8_X4_X4 = auto()
    X4_X4_X8 = auto()
    X4_X4_X4_X4 = auto()
    X2_X2_X2_X2_X2_X2_X2_X2 = auto()
    X8_X4_X2_X2 = auto()
    X8_X2_X2_X4 = auto()
    X2_X2_X4_X8 = auto()
    X4_X2_X2_X8 = auto()
    X2_X2_X2_X2_X8 = auto()
    X8_X2_X2_X2_X2 = auto()
    X2_X2_X4_X4_X4 = auto()
    X4_X2_X2_X4_X4 = auto()
    X4_X4_X2_X2_X4 = auto()
    X4_X4_X4_X2_X2 = auto()
    X2_X2_X2_X2_X4_X4 = auto()
    X2_X2_X4_X2_X2_X4 = auto()
    X4_X2_X2_X2_X2_X4 = auto()
    X2_X2_X4_X4_X2_X2 = auto()
    X4_X2_X2_X4_X2_X2 = auto()
    X4_X4_X2_X2_X2_X2 = auto()
    X2_X2_X2_X2_X2_X2_X4 = auto()
    X2_X2_X2_X2_X4_X2_X2 = auto()
    X2_X2_X4_X2_X2_X2_X2 = auto()
    X4_X2_X2_X2_X2_X2_X2 = auto()
    X4_X4 = auto()
    X2_X2_X4 = auto()
    X4_X2_X2 = auto()
    X2_X2_X2_X2 = auto()
    X2_X2 = auto()

    @property
    def total_lanes(self) -> int:
        """Return total lanes used by this bifurcation mode."""
        name = self.name
        parts = name.split("_")
        return sum(int(p[1:]) for p in parts if p.startswith("X"))


class PCIeGeneration(IntEnum):
    """PCIe generation version."""

    RESERVED = 0
    GEN1 = auto()
    GEN2 = auto()
    GEN3 = auto()
    GEN4 = auto()
    GEN5 = auto()
    GEN6 = auto()


class GlobalInterruptMask(IntEnum):
    """Global interrupt mask bits."""

    GLOBAL = 0
    EQ_PHASE_ERR = auto()
    PHASE_ERR = auto()
    INTERNAL_ERR = auto()


class InternalErrorMask(IntEnum):
    """Internal error mask bits."""

    TX_PLL_UNLOCK = 0
    US_RX_CDR_UNLOCK = auto()
    DS_RX_CDR_UNLOCK = auto()
    CMU_PLL_UNLOCK = auto()
    PLL_SSC_UNLOCK = auto()
    WDT_TIMEOUT_INTR = auto()
    SMBUS_ACCESS_ERR = auto()


class LTSSMStateMask(IntEnum):
    """LTSSM state indicator mask bits."""

    EIE = 0  # Electrical Idle Exit
    RECOVERY = auto()
    CONFIG = auto()
    LOOPBACK = auto()


class RxErrorMask(IntEnum):
    """RX error mask bits."""

    INVALID_SYMBOL = 0
    SYMBOL_LOCK = auto()
    ELASTIC_BUF_OVER_UNDER_FLOW = auto()
    LANE_TO_LANE_DESKEW = auto()
    LOSS_BLOCK_ALIGNMENT = auto()
    BLOCK_HEADER = auto()
    SOS_BLOCK_ERROR = auto()


class TxEqTimeoutMask(IntEnum):
    """TX equalization timeout mask bits."""

    PH1 = 0
    PH2_GEN3 = auto()
    PH3_GEN3 = auto()
    PH2_GEN4 = auto()
    PH3_GEN4 = auto()
    PH2_GEN5 = auto()
    PH3_GEN5 = auto()
    PH2_GEN6 = auto()
    PH3_GEN6 = auto()


class LTSSMState(IntEnum):
    """Current LTSSM state values."""

    # Reset Exit Startup States
    DETECT = 0x0
    RATE_CHANGE = 0x3
    # Forwarding States
    FWD_FORWARDING = 0x4
    FWD_HOT_RESET = 0x5
    FWD_DISABLE = 0x6
    FWD_LOOPBACK = 0x7
    FWD_CPL_RCV = 0x8
    FWD_ENTER_CPL = 0x9
    FWD_PM_L1_1 = 0xA
    # Execution States
    EXE_CLB_ENTRY = 0x10
    EXE_CLB_PATTERN = 0x11
    EXE_CLB_EXIT = 0x12
    EXE_EQ_PH2_ACTIVE = 0x14
    EXE_EQ_PH2_PASSIVE = 0x15
    EXE_EQ_PH3_ACTIVE = 0x16
    EXE_EQ_PH3_PASSIVE = 0x17
    EXE_EQ_FORCE_TIMEOUT = 0x18
    EXE_SLAVE_LPBK_ENTRY = 0x1C
    EXE_SLAVE_LPBK_ACTIVE = 0x1D
    EXE_SLAVE_LPBK_EXIT = 0x1E


class PRBSPattern(IntEnum):
    """PRBS polynomial patterns."""

    PRBS7 = 0
    PRBS9 = auto()
    PRBS10 = auto()
    PRBS11 = auto()
    PRBS13 = auto()
    PRBS15 = auto()
    PRBS20 = auto()
    PRBS23 = auto()
    PRBS31 = auto()
    PRBS49 = auto()
    PRBS58 = auto()


class ELAType(IntEnum):
    """ELA (Embedded Logic Analyzer) type."""

    LANE_PIPE_A = 0
    LANE_PIPE_B = auto()
    PSEUDO_PORT = auto()
    PSEUDO_PORT_A = auto()
    PSEUDO_PORT_B = auto()


class ELATriggerPosition(IntEnum):
    """ELA trigger position percentage."""

    POS_00 = 0  # 0%
    POS_25 = auto()  # 25%
    POS_50 = auto()  # 50%
    POS_75 = auto()  # 75%


class ELATriggerType(IntEnum):
    """ELA trigger type."""

    RISING = 0
    FALLING = auto()
    PATTERN = auto()


class BELAStatus(IntEnum):
    """BELA (Broadcom Embedded Logic Analyzer) status."""

    RESERVED = 0
    BUSY = 1
    TRIGGERED = 2
    ABORTED = 3
    INVALID = 7


class BELAState(IntEnum):
    """BELA state machine states."""

    INIT = 0
    STANDBY = auto()
    START = auto()
    HUNT = auto()
    CAPTURE = auto()
    AUTORESTART = auto()


class BELATriggerType(IntEnum):
    """BELA trigger types."""

    LIVE_DATARATE = 0
    DATARATE_ENTRY = auto()
    DATARATE_EXIT = auto()
    DATARATE_ENTRY_EXIT = auto()


class BELAPreTriggerLength(IntEnum):
    """BELA pre-trigger length."""

    LEN_0 = 0  # No pre-trigger samples
    LEN_1_8 = auto()  # 1/8th of buffer
    LEN_1_2 = auto()  # 1/2 of buffer
    LEN_7_8 = auto()  # 7/8th of buffer


class BELALaneWidth(IntEnum):
    """BELA lane width values."""

    INVALID = 0
    WIDTH_2 = auto()
    WIDTH_4 = auto()
    WIDTH_8 = auto()
    WIDTH_16 = auto()


class FWUploadStatus(IntEnum):
    """Firmware upload status."""

    RESERVED = 0
    DONE = auto()
    BUSY = auto()
    NO_NVM = auto()
    MEM_UNAVAIL = auto()


class LinkCATMode(IntEnum):
    """LinkCAT operation modes."""

    LP_TX = 0
    LOOPBACK = auto()
    PRE_RX = auto()
    RX_MEASURE = auto()


class RecoveryCounterConfig(IntEnum):
    """Recovery counter configuration."""

    DISABLE = 0
    ENABLE = auto()
    CLEAR = auto()


class DebugLevel(IntEnum):
    """Debug log level."""

    NONE = 0
    DEBUG = 1
    VERBOSE = 2
    FUNCTIONS = 4


class DebugOutputType(IntEnum):
    """Debug output type."""

    CONSOLE = 0
    FILE = auto()


class RegisterType(IntEnum):
    """Register block type."""

    RESERVED = 0
    MAC = auto()
    SERDES = auto()
    PIPE = auto()
    CMU = auto()


class EyeMarginType(IntEnum):
    """Eye margin types."""

    LOWER = 0
    MIDDLE = auto()
    UPPER = auto()


class ConfigOption(IntEnum):
    """Configuration options for get/set operations."""

    STATIC = 0
    PORT_ORIENTATION = auto()
    MAX_DATA_RATE = auto()
    BIFURCATION_MODE = auto()
    CLOCKING_MODE = auto()
    GLOBAL_INTERRUPT_MASK = auto()
    GLOBAL_INTERRUPT_STS = auto()
    INTERNAL_ERROR_MASK = auto()
    INTERNAL_ERROR_STS = auto()
    LTSSM_MASK = auto()
    LTSSM_STS = auto()
    RX_ERROR_MASK = auto()
    RX_ERROR_STS = auto()
    TX_EQ_TIMEOUT_MASK = auto()
    TX_EQ_TIMEOUT_STS = auto()


class ForwardingMode(IntEnum):
    """Forwarding mode status."""

    DISABLED = 0
    ENABLED = auto()


class PortType(IntEnum):
    """Port type (upstream/downstream)."""

    UNKNOWN = 0
    UPSTREAM = auto()
    DOWNSTREAM = auto()


class LinkState(IntEnum):
    """Link state."""

    DOWN = 0
    UP = auto()
