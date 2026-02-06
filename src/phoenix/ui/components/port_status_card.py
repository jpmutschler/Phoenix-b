"""
Port status card component showing LTSSM state, speed, width, and forwarding.
"""

from nicegui import ui

from phoenix.models.status import PortStatus
from phoenix.ui.theme import COLORS, link_color
from phoenix.ui.components.status_indicator import status_dot, link_status_badge


def render_port_status_card(port: PortStatus, label: str = "Port") -> None:
    """Render a port status card.

    Args:
        port: Port status model.
        label: Display label (e.g., 'PPA' or 'PPB').
    """
    is_up = port.is_link_up
    color = link_color(is_up)

    with ui.card().classes("w-full q-pa-md"):
        with ui.row().classes("w-full items-center justify-between q-mb-sm"):
            with ui.row().classes("items-center q-gutter-sm"):
                ui.icon("settings_ethernet").style(
                    f"color: {color}; font-size: 1.3rem;"
                )
                ui.label(label).classes("text-h6").style(
                    f"color: {COLORS.text_primary};"
                )
            link_status_badge(is_up)

        with ui.grid(columns=2).classes("w-full q-gutter-y-xs"):
            _stat_row("LTSSM State", port.current_ltssm_state.name)
            _stat_row("Link Speed", port.current_link_speed.name if port.current_link_speed else "N/A")
            _stat_row("Link Width", f"x{port.current_link_width}")
            _stat_row("Forwarding", "Enabled" if port.is_forwarding else "Disabled")
            _stat_row("Port Type", port.port_type.name)
            _stat_row("Enabled Lanes", str(port.enabled_lanes))


def _stat_row(label: str, value: str) -> None:
    """Render a label: value stat row."""
    ui.label(label).classes("text-caption").style(
        f"color: {COLORS.text_muted};"
    )
    ui.label(value).classes("text-body2 mono").style(
        f"color: {COLORS.text_primary};"
    )
