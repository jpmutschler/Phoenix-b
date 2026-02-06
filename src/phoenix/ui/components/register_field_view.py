"""
Bit-field decode visualization for register values.

Shows a visual breakdown of register fields with their values.
"""

from nicegui import ui

from phoenix.protocol.register_maps import Register, RegisterField
from phoenix.ui.theme import COLORS


def render_register_fields(register: Register, value: int) -> None:
    """Render a visual field-level decode of a register value.

    Args:
        register: Register definition with field metadata.
        value: Raw register value to decode.
    """
    if not register.fields:
        ui.label("No field definitions").style(f"color: {COLORS.text_muted};")
        return

    # Field table
    columns = [
        {"name": "field", "label": "Field", "field": "field", "align": "left"},
        {"name": "bits", "label": "Bits", "field": "bits", "align": "center"},
        {"name": "hex", "label": "Hex", "field": "hex", "align": "center"},
        {"name": "dec", "label": "Decimal", "field": "dec", "align": "center"},
        {"name": "desc", "label": "Description", "field": "desc", "align": "left"},
    ]

    rows = []
    for field in register.fields:
        field_val = field.extract(value)
        hex_digits = max(1, (field.bit_width + 3) // 4)
        bit_range = (
            f"[{field.bit_offset + field.bit_width - 1}:{field.bit_offset}]"
            if field.bit_width > 1
            else f"[{field.bit_offset}]"
        )
        rows.append({
            "field": field.name,
            "bits": bit_range,
            "hex": f"0x{field_val:0{hex_digits}X}",
            "dec": str(field_val),
            "desc": field.description,
        })

    ui.table(
        columns=columns,
        rows=rows,
        row_key="field",
    ).classes("w-full").props("dense flat bordered")

    # Bit-level visualization
    _render_bit_map(register, value)


def _render_bit_map(register: Register, value: int) -> None:
    """Render a horizontal bit-map visualization."""
    bit_width = register.size * 8

    # Assign colors to fields
    field_colors = [
        COLORS.cyan, COLORS.blue, COLORS.purple, COLORS.green,
        COLORS.yellow, COLORS.orange, COLORS.red,
    ]

    ui.label("BIT MAP").classes("section-title q-mt-md")

    with ui.row().classes("q-gutter-none").style("flex-wrap: wrap;"):
        for bit in range(bit_width - 1, -1, -1):
            bit_val = (value >> bit) & 1
            field_info = _field_at_bit(register, bit)

            if field_info is not None:
                field_idx = list(register.fields).index(field_info)
                bg = field_colors[field_idx % len(field_colors)]
                opacity = "1.0" if bit_val else "0.3"
            else:
                bg = COLORS.text_muted
                opacity = "0.2"

            with ui.element("div").style(
                f"width: 18px; height: 22px; "
                f"background-color: {bg}; opacity: {opacity}; "
                f"border: 1px solid {COLORS.bg_primary}; "
                f"display: flex; align-items: center; justify-content: center;"
            ).tooltip(
                f"Bit {bit}: {bit_val}"
                + (f" ({field_info.name})" if field_info else "")
            ):
                if bit % 8 == 0:
                    ui.label(str(bit)).style(
                        "font-size: 0.5rem; color: white; font-weight: 600;"
                    )


def _field_at_bit(register: Register, bit: int):
    """Find the field that contains the given bit position."""
    for field in register.fields:
        if field.bit_offset <= bit < field.bit_offset + field.bit_width:
            return field
    return None
