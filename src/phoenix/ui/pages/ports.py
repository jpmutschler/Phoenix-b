"""
Port detail page with PPA/PPB side-by-side and 16-lane grid.

Route: /device/{handle}/ports
"""

from nicegui import ui

from phoenix.api.app import get_device
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS
from phoenix.ui.components.port_status_card import render_port_status_card
from phoenix.ui.components.lane_grid import render_lane_grid
from phoenix.ui.components.status_indicator import status_badge


def ports_page(handle: int) -> None:
    """Render the ports detail page."""

    ppa_container = None
    ppb_container = None
    ppa_lanes_container = None
    ppb_lanes_container = None
    ltssm_table_container = None
    error_label = None

    def build_content():
        nonlocal ppa_container, ppb_container, ppa_lanes_container
        nonlocal ppb_lanes_container, ltssm_table_container, error_label

        error_label = ui.label("").style(f"color: {COLORS.red};").classes("q-mb-sm")
        error_label.visible = False

        ui.label("Port Status").classes("text-h5 q-mb-md").style(
            f"color: {COLORS.text_primary};"
        )

        # Port cards side by side
        with ui.row().classes("w-full q-gutter-md"):
            with ui.column().classes("col"):
                ppa_container = ui.column().classes("w-full")
                with ui.card().classes("w-full q-pa-md q-mt-md"):
                    ui.label("PPA LANE STATUS").classes("section-title")
                    ppa_lanes_container = ui.column().classes("w-full")

            with ui.column().classes("col"):
                ppb_container = ui.column().classes("w-full")
                with ui.card().classes("w-full q-pa-md q-mt-md"):
                    ui.label("PPB LANE STATUS").classes("section-title")
                    ppb_lanes_container = ui.column().classes("w-full")

        # LTSSM state reference table
        with ui.card().classes("w-full q-pa-md q-mt-lg"):
            ui.label("LTSSM STATE REFERENCE").classes("section-title")
            ltssm_table_container = ui.column().classes("w-full")

        _render_ltssm_table(ltssm_table_container)

        # Polling timer (pass async func directly, not via lambda)
        ui.timer(2.0, refresh_ports)

    async def refresh_ports():
        try:
            device = get_device(handle)
            status = await device.get_status()

            ppa_container.clear()
            with ppa_container:
                render_port_status_card(status.ppa_status, "Pseudo Port A (PPA)")

            ppb_container.clear()
            with ppb_container:
                render_port_status_card(status.ppb_status, "Pseudo Port B (PPB)")

            ppa_lanes_container.clear()
            with ppa_lanes_container:
                render_lane_grid(status.ppa_status.lane_status)

            ppb_lanes_container.clear()
            with ppb_lanes_container:
                render_lane_grid(status.ppb_status.lane_status)

            error_label.visible = False

        except Exception as e:
            error_label.text = f"Failed to read port status: {e}"
            error_label.visible = True

    page_layout(
        title="Port Status",
        handle=handle,
        content_builder=build_content,
    )


def _render_ltssm_table(container) -> None:
    """Render LTSSM state reference table."""
    from phoenix.protocol.enums import LTSSMState

    columns = [
        {"name": "value", "label": "Value", "field": "value", "align": "center"},
        {"name": "name", "label": "State", "field": "name", "align": "left"},
        {"name": "category", "label": "Category", "field": "category", "align": "left"},
    ]

    rows = []
    for state in LTSSMState:
        if state.value < 0x10:
            category = "Reset/Startup" if state.value < 0x4 else "Forwarding"
        else:
            category = "Execution"

        rows.append({
            "value": f"0x{state.value:02X}",
            "name": state.name,
            "category": category,
        })

    with container:
        ui.table(
            columns=columns,
            rows=rows,
            row_key="name",
        ).classes("w-full").props("dense flat bordered")
