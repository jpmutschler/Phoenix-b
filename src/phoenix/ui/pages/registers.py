"""Register browser page with named register table and direct hex read/write.

Route: /device/{handle}/registers
"""

from nicegui import ui

from phoenix.api.app import get_device
from phoenix.protocol.chip_profile import load_profile
from phoenix.protocol.register_maps import Register
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS
from phoenix.ui.components.hex_display import hex_label
from phoenix.ui.components.register_field_view import render_register_fields


def registers_page(handle: int) -> None:
    """Render the register browser page."""

    profile = load_profile()
    registers = profile.registers

    reg_table_container = None
    detail_container = None
    direct_result = None
    status_label = None

    def build_content():
        nonlocal reg_table_container, detail_container, direct_result, status_label

        ui.label("Register Browser").classes("text-h5 q-mb-md").style(
            f"color: {COLORS.text_primary};"
        )

        # Direct register access section
        with ui.card().classes("w-full q-pa-md q-mb-lg"):
            ui.label("DIRECT REGISTER ACCESS").classes("section-title")

            with ui.row().classes("w-full q-gutter-md items-end"):
                addr_input = ui.input(
                    "Address (hex)",
                    value="0x0000",
                    placeholder="0x0000",
                ).classes("col-3")

                width_select = ui.select(
                    {32: "32-bit", 16: "16-bit"},
                    value=32,
                    label="Width",
                ).classes("col-2")

                value_input = ui.input(
                    "Value (hex, for write)",
                    value="",
                    placeholder="0x00000000",
                ).classes("col-3")

                read_btn = ui.button("Read", icon="download").props("color=primary")
                write_btn = ui.button("Write", icon="upload").props("color=warning")

            direct_result = ui.column().classes("w-full q-mt-sm")

            status_label = ui.label("").classes("text-caption q-mt-sm").style(
                f"color: {COLORS.text_secondary};"
            )

            async def do_read():
                read_btn.props("loading")
                try:
                    device = get_device(handle)
                    addr_str = addr_input.value.strip()
                    addr = int(addr_str, 16) if addr_str.startswith("0x") else int(addr_str)
                    width = int(width_select.value)

                    value = await device.read_register(addr, width)

                    direct_result.clear()
                    with direct_result:
                        with ui.row().classes("items-center q-gutter-md"):
                            ui.label(f"0x{addr:04X} =").classes("mono").style(
                                f"color: {COLORS.text_secondary};"
                            )
                            hex_label(value, width)

                        # Check if this matches a named register
                        named = _find_register_by_address(addr, registers)
                        if named is not None:
                            ui.label(f"({named.name})").classes("text-caption").style(
                                f"color: {COLORS.text_muted};"
                            )
                            render_register_fields(named, value)

                    status_label.text = f"Read 0x{addr:04X} = 0x{value:0{width // 4}X}"
                    status_label.style(f"color: {COLORS.green};")

                except Exception as e:
                    status_label.text = f"Read failed: {e}"
                    status_label.style(f"color: {COLORS.red};")
                finally:
                    read_btn.props(remove="loading")

            async def do_write():
                write_btn.props("loading")
                try:
                    device = get_device(handle)
                    addr_str = addr_input.value.strip()
                    addr = int(addr_str, 16) if addr_str.startswith("0x") else int(addr_str)
                    val_str = value_input.value.strip()
                    if not val_str:
                        status_label.text = "Enter a value to write."
                        status_label.style(f"color: {COLORS.yellow};")
                        return
                    val = int(val_str, 16) if val_str.startswith("0x") else int(val_str)
                    width = int(width_select.value)

                    await device.write_register(addr, val, width)

                    status_label.text = f"Wrote 0x{val:0{width // 4}X} to 0x{addr:04X}"
                    status_label.style(f"color: {COLORS.green};")

                except Exception as e:
                    status_label.text = f"Write failed: {e}"
                    status_label.style(f"color: {COLORS.red};")
                finally:
                    write_btn.props(remove="loading")

            read_btn.on_click(do_read)
            write_btn.on_click(do_write)

        # Named register table
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            ui.label("NAMED REGISTERS").classes("section-title")
            ui.label(
                "Click a register to read its current value and decode fields."
            ).classes("text-caption q-mb-md").style(f"color: {COLORS.text_muted};")

            reg_table_container = ui.column().classes("w-full")
            _build_register_table(reg_table_container, handle, registers)

        # Field decode detail area
        detail_container = ui.column().classes("w-full")

    def _build_register_table(container, dev_handle: int, regs: dict[str, Register]):
        """Build the named register table."""
        columns = [
            {"name": "name", "label": "Register", "field": "name", "align": "left", "sortable": True},
            {"name": "address", "label": "Address", "field": "address", "align": "center"},
            {"name": "size", "label": "Size", "field": "size", "align": "center"},
            {"name": "description", "label": "Description", "field": "description", "align": "left"},
            {"name": "fields", "label": "Fields", "field": "fields", "align": "center"},
        ]

        rows = []
        for name, reg in regs.items():
            rows.append({
                "name": name,
                "address": f"0x{reg.address:04X}",
                "size": f"{reg.size * 8}-bit",
                "description": reg.description,
                "fields": str(len(reg.fields)),
            })

        with container:
            table = ui.table(
                columns=columns,
                rows=rows,
                row_key="name",
                selection="single",
            ).classes("w-full").props("dense flat bordered")

            async def on_select(e):
                await _on_register_selected(e, dev_handle, regs)

            table.on_select(on_select)

    async def _on_register_selected(event, dev_handle: int, regs: dict[str, Register]):
        """Handle register row selection -- read and decode."""
        # NiceGUI 2.x passes event.selection as a list of selected row dicts
        selected = getattr(event, "selection", None)
        if not selected:
            # Fallback: try event.args for compatibility
            selected = (event.args or {}).get("rows", [])
        if not selected:
            return

        reg_name = selected[0].get("name")
        if reg_name not in regs:
            return

        reg = regs[reg_name]

        try:
            device = get_device(dev_handle)
            width = reg.size * 8
            value = await device.read_register(reg.address, width)

            detail_container.clear()
            with detail_container:
                with ui.card().classes("w-full q-pa-md"):
                    with ui.row().classes("items-center q-gutter-md q-mb-md"):
                        ui.label(reg.name).classes("text-h6").style(
                            f"color: {COLORS.text_primary};"
                        )
                        ui.label(f"0x{reg.address:04X}").classes("mono text-caption").style(
                            f"color: {COLORS.text_muted};"
                        )
                        ui.label("=").style(f"color: {COLORS.text_muted};")
                        hex_label(value, width)

                    ui.label(reg.description).classes("text-body2 q-mb-md").style(
                        f"color: {COLORS.text_secondary};"
                    )

                    render_register_fields(reg, value)

        except Exception as e:
            detail_container.clear()
            with detail_container:
                ui.label(f"Failed to read register: {e}").style(
                    f"color: {COLORS.red};"
                )

    page_layout(
        title="Register Browser",
        handle=handle,
        content_builder=build_content,
    )


def _find_register_by_address(address: int, registers: dict[str, Register]):
    """Find a named register by address."""
    for reg in registers.values():
        if reg.address == address:
            return reg
    return None
