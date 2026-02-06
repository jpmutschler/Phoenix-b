"""
Monospaced hex value display component.
"""

from nicegui import ui

from phoenix.ui.theme import COLORS


def hex_label(value: int, width: int = 32, prefix: bool = True) -> ui.label:
    """Render a hex value in monospaced cyan text.

    Args:
        value: Integer value to display.
        width: Bit width (determines hex digit count).
        prefix: Include '0x' prefix.
    """
    digits = width // 4
    prefix_str = "0x" if prefix else ""
    text = f"{prefix_str}{value:0{digits}X}"
    return ui.label(text).classes("hex-value mono")


def hex_address_value(address: int, value: int, width: int = 32) -> None:
    """Render an address: value pair in hex."""
    with ui.row().classes("items-center q-gutter-sm mono"):
        ui.label(f"0x{address:04X}").style(
            f"color: {COLORS.text_secondary};"
        )
        ui.label("=").style(f"color: {COLORS.text_muted};")
        hex_label(value, width)


def register_value_display(
    name: str, address: int, value: int, width: int = 32,
) -> None:
    """Render a named register with address and value."""
    with ui.row().classes("w-full items-center justify-between q-py-xs"):
        with ui.row().classes("items-center q-gutter-sm"):
            ui.label(name).style(f"color: {COLORS.text_primary}; font-size: 0.85rem;")
            ui.label(f"(0x{address:04X})").classes("text-caption").style(
                f"color: {COLORS.text_muted};"
            )
        hex_label(value, width)
