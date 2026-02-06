"""Generic register map types for retimer register access.

Defines Register, RegisterField, and RegisterAccess generic dataclasses.
Chip-specific register definitions are loaded at runtime via ChipProfile.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RegisterField:
    """Definition of a field within a register."""

    name: str
    bit_offset: int
    bit_width: int
    description: str = ""

    @property
    def mask(self) -> int:
        """Return the bit mask for this field."""
        return ((1 << self.bit_width) - 1) << self.bit_offset

    def extract(self, value: int) -> int:
        """Extract field value from register value."""
        return (value >> self.bit_offset) & ((1 << self.bit_width) - 1)

    def insert(self, reg_value: int, field_value: int) -> int:
        """Insert field value into register value."""
        cleared = reg_value & ~self.mask
        inserted = (field_value & ((1 << self.bit_width) - 1)) << self.bit_offset
        return cleared | inserted


@dataclass(frozen=True)
class Register:
    """Definition of a register."""

    name: str
    address: int
    size: int = 4  # Size in bytes (default 32-bit)
    description: str = ""
    fields: tuple[RegisterField, ...] = ()

    def get_field(self, name: str) -> Optional[RegisterField]:
        """Get a field by name."""
        for field in self.fields:
            if field.name == name:
                return field
        return None


class RegisterAccess:
    """Helper class for register field access."""

    @staticmethod
    def get_field_value(register: Register, reg_value: int, field_name: str) -> int:
        """Extract a field value from a register value.

        Args:
            register: Register definition
            reg_value: Raw register value
            field_name: Name of field to extract

        Returns:
            Field value

        Raises:
            ValueError: If field not found
        """
        field = register.get_field(field_name)
        if field is None:
            raise ValueError(f"Field '{field_name}' not found in register '{register.name}'")
        return field.extract(reg_value)

    @staticmethod
    def set_field_value(
        register: Register, reg_value: int, field_name: str, field_value: int
    ) -> int:
        """Set a field value in a register value.

        Args:
            register: Register definition
            reg_value: Current register value
            field_name: Name of field to set
            field_value: Value to set

        Returns:
            Modified register value

        Raises:
            ValueError: If field not found
        """
        field = register.get_field(field_name)
        if field is None:
            raise ValueError(f"Field '{field_name}' not found in register '{register.name}'")
        return field.insert(reg_value, field_value)
