"""
Real-time status dashboard page.

Route: /device/{handle}
Polls device status every 2 seconds via ui.timer().
"""

from nicegui import ui

from phoenix.api.app import get_device
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS, temp_color, temp_status
from phoenix.ui.components.status_indicator import health_badge, status_badge
from phoenix.ui.components.temperature_gauge import (
    render_temperature_gauge,
    update_temperature_gauge,
)
from phoenix.ui.components.voltage_chart import (
    render_voltage_chart,
    update_voltage_chart,
)
from phoenix.ui.components.port_status_card import render_port_status_card


def dashboard_page(handle: int) -> None:
    """Render the real-time dashboard page."""

    temp_gauge = None
    volt_chart = None
    health_container = None
    interrupt_container = None
    fw_label = None
    ppa_container = None
    ppb_container = None
    error_label = None

    def build_content():
        nonlocal temp_gauge, volt_chart, health_container, interrupt_container
        nonlocal fw_label, ppa_container, ppb_container, error_label

        # Error area
        error_label = ui.label("").style(f"color: {COLORS.red};").classes("q-mb-sm")
        error_label.visible = False

        # Top row: health + firmware info
        with ui.row().classes("w-full items-center q-gutter-md q-mb-md"):
            health_container = ui.row().classes("items-center q-gutter-sm")
            ui.space()
            fw_label = ui.label("").classes("text-caption mono").style(
                f"color: {COLORS.text_secondary};"
            )

        # Main grid
        with ui.row().classes("w-full q-gutter-md"):
            # Left column: temp + voltage
            with ui.column().classes("col q-gutter-md"):
                with ui.card().classes("w-full q-pa-md"):
                    ui.label("TEMPERATURE").classes("section-title")
                    temp_gauge = render_temperature_gauge(0)

                with ui.card().classes("w-full q-pa-md"):
                    ui.label("VOLTAGE RAILS").classes("section-title")
                    volt_chart = render_voltage_chart()

            # Right column: ports + interrupts
            with ui.column().classes("col q-gutter-md"):
                ppa_container = ui.column().classes("w-full")
                ppb_container = ui.column().classes("w-full")

                with ui.card().classes("w-full q-pa-md"):
                    ui.label("INTERRUPTS").classes("section-title")
                    interrupt_container = ui.column().classes("w-full q-gutter-xs")

        # Timer for real-time updates (pass async func directly, not via lambda)
        ui.timer(2.0, refresh_status)

    async def refresh_status():
        try:
            device = get_device(handle)
            status = await device.get_status()

            # Update temperature gauge
            update_temperature_gauge(temp_gauge, status.temperature_c)

            # Update voltage chart
            update_voltage_chart(volt_chart, status.voltage_info)

            # Update health badge
            health_container.clear()
            with health_container:
                health_badge(status.is_healthy)
                color = temp_color(status.temperature_c)
                status_badge(
                    f"{status.temperature_c}°C ({temp_status(status.temperature_c)})",
                    color,
                )

            # Firmware info
            device_info = device.device_info
            fw_label.text = (
                f"FW {device_info.firmware_version_str} | "
                f"Handle {device_info.product_handle} | "
                f"Addr 0x{device_info.device_address:02X}"
            )

            # Update port cards
            ppa_container.clear()
            with ppa_container:
                render_port_status_card(status.ppa_status, "Pseudo Port A (PPA)")

            ppb_container.clear()
            with ppb_container:
                render_port_status_card(status.ppb_status, "Pseudo Port B (PPB)")

            # Update interrupts
            interrupt_container.clear()
            with interrupt_container:
                intr = status.interrupt_status
                _interrupt_row("Global Interrupt", intr.global_interrupt)
                _interrupt_row("EQ Phase Error", intr.eq_phase_error)
                _interrupt_row("PHY Phase Error", intr.phy_phase_error)
                _interrupt_row("Internal Error", intr.internal_error)

            # Clear error
            error_label.visible = False

        except Exception as e:
            error_label.text = f"Failed to read device: {e}"
            error_label.visible = True

    page_layout(
        title="Dashboard",
        handle=handle,
        content_builder=build_content,
    )


def _interrupt_row(name: str, is_set: bool) -> None:
    """Render a single interrupt status row."""
    color = COLORS.red if is_set else COLORS.green
    icon_name = "error" if is_set else "check_circle"
    text = "SET" if is_set else "CLEAR"

    with ui.row().classes("items-center q-gutter-sm"):
        ui.icon(icon_name).style(f"color: {color}; font-size: 1rem;")
        ui.label(name).style(f"color: {COLORS.text_primary}; font-size: 0.85rem;")
        ui.space()
        ui.label(text).classes("text-caption mono").style(f"color: {color};")
