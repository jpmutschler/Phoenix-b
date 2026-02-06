"""Chip profile loader for retimer register maps and command definitions.

Loads proprietary chip data from JSON data files, keeping register addresses,
field definitions, and SMBus command codes out of Python source.
"""

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Optional

from phoenix.protocol.register_maps import Register, RegisterField


@dataclass(frozen=True)
class TxCoeffLayout:
    """TX coefficient address layout."""

    gen3_base: int
    gen4_base: int
    gen5_base: int
    gen6_base: int
    lane_stride: int


@dataclass(frozen=True)
class ErrorStatsLayout:
    """Error statistics address layout."""

    base: int
    lane_stride: int


@dataclass(frozen=True)
class ChipProfile:
    """Immutable profile containing all chip-specific register and command data."""

    name: str
    vendor_id: int
    device_id: int
    registers: dict[str, Register]
    register_blocks: dict[str, int]
    tx_coefficients: TxCoeffLayout
    error_stats: ErrorStatsLayout
    smbus_commands: dict[str, int]

    def get_register(self, short_name: str) -> Register:
        """Look up a register by short name.

        Args:
            short_name: Register short name (e.g. "GLOBAL_PARAM0")

        Returns:
            Register definition

        Raises:
            KeyError: If register not found
        """
        if short_name not in self.registers:
            raise KeyError(f"Register '{short_name}' not found in profile '{self.name}'")
        return self.registers[short_name]

    def get_tx_coeff_address(self, gen: int, lane: int, offset: int = 0) -> int:
        """Calculate TX coefficient register address.

        Args:
            gen: PCIe generation (3, 4, 5, 6)
            lane: Lane number (0-15)
            offset: Register offset within lane block

        Returns:
            Register address
        """
        base_map = {
            3: self.tx_coefficients.gen3_base,
            4: self.tx_coefficients.gen4_base,
            5: self.tx_coefficients.gen5_base,
            6: self.tx_coefficients.gen6_base,
        }
        base = base_map.get(gen, self.tx_coefficients.gen3_base)
        return base + (lane * self.tx_coefficients.lane_stride) + offset

    def get_error_stats_address(self, lane: int, error_type: int = 0) -> int:
        """Calculate error statistics register address.

        Args:
            lane: Lane number (0-15)
            error_type: Error type index (0-47)

        Returns:
            Register address
        """
        return (
            self.error_stats.base
            + (lane * self.error_stats.lane_stride)
            + (error_type * 4)
        )

    def get_smbus_command(self, name: str) -> int:
        """Look up an SMBus command code by name.

        Args:
            name: Command name (e.g. "WR32_2ADDR_PEC")

        Returns:
            Command byte value

        Raises:
            KeyError: If command not found
        """
        if name not in self.smbus_commands:
            raise KeyError(f"SMBus command '{name}' not found in profile '{self.name}'")
        return self.smbus_commands[name]


def _parse_hex(value: str) -> int:
    """Parse a hex string (e.g. '0x14E4') to int."""
    return int(value, 16)


def _build_register(short_name: str, data: dict) -> Register:
    """Build a Register from JSON dict."""
    fields = tuple(
        RegisterField(
            name=f["name"],
            bit_offset=f["bit_offset"],
            bit_width=f["bit_width"],
            description=f.get("description", ""),
        )
        for f in data.get("fields", [])
    )
    return Register(
        name=data["name"],
        address=_parse_hex(data["address"]),
        size=data.get("size", 4),
        description=data.get("description", ""),
        fields=fields,
    )


def _load_profile_from_json(raw: dict) -> ChipProfile:
    """Build a ChipProfile from parsed JSON data."""
    chip = raw["chip"]

    registers = {
        short_name: _build_register(short_name, reg_data)
        for short_name, reg_data in raw["registers"].items()
    }

    register_blocks = {
        name: _parse_hex(addr) for name, addr in raw["register_blocks"].items()
    }

    tx = raw["tx_coefficients"]
    tx_coefficients = TxCoeffLayout(
        gen3_base=_parse_hex(tx["gen3_base"]),
        gen4_base=_parse_hex(tx["gen4_base"]),
        gen5_base=_parse_hex(tx["gen5_base"]),
        gen6_base=_parse_hex(tx["gen6_base"]),
        lane_stride=_parse_hex(tx["lane_stride"]),
    )

    es = raw["error_stats"]
    error_stats = ErrorStatsLayout(
        base=_parse_hex(es["base"]),
        lane_stride=_parse_hex(es["lane_stride"]),
    )

    smbus_commands = {
        name: _parse_hex(code) for name, code in raw["smbus_commands"].items()
    }

    return ChipProfile(
        name=chip["name"],
        vendor_id=_parse_hex(chip["vendor_id"]),
        device_id=_parse_hex(chip["device_id"]),
        registers=registers,
        register_blocks=register_blocks,
        tx_coefficients=tx_coefficients,
        error_stats=error_stats,
        smbus_commands=smbus_commands,
    )


@lru_cache(maxsize=1)
def load_profile(name: str = "bcm85667") -> ChipProfile:
    """Load a chip profile from the bundled JSON data file.

    The result is cached after the first call so the JSON is read only once
    per process.

    Args:
        name: Profile name (matches JSON filename without extension)

    Returns:
        Loaded ChipProfile

    Raises:
        FileNotFoundError: If profile JSON not found
        KeyError: If required keys missing from JSON
    """
    data_files = resources.files("phoenix.data")
    json_path = data_files.joinpath(f"{name}.json")

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    return _load_profile_from_json(raw)
