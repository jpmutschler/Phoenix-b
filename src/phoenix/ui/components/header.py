"""
Top header bar: branding, page title, and connection status badge.
"""

from typing import Optional

from nicegui import ui

from phoenix.api.app import _connected_devices
from phoenix.ui.theme import COLORS


def render_header(title: str, handle: Optional[int] = None) -> None:
    """Render the top header bar.

    Args:
        title: Current page title.
        handle: Connected device handle, if any.
    """
    with ui.row().classes("w-full items-center no-wrap q-gutter-md"):
        # Brand
        ui.image("/static/logo.png").classes("").style(
            "width: 32px; height: 32px; object-fit: contain;"
        )
        ui.label("PHOENIX").classes("text-h6 text-bold").style(
            f"color: {COLORS.cyan}; letter-spacing: 0.15em;"
        )
        ui.label("|").style(f"color: {COLORS.text_muted};")
        ui.label("Serial Cables Gen6 PCIe/CXL Retimer (Broadcom)").classes("text-subtitle2").style(
            f"color: {COLORS.text_secondary};"
        )

        ui.space()

        # Page title
        ui.label(title).classes("text-subtitle1").style(
            f"color: {COLORS.text_primary};"
        )

        ui.space()

        # Connection badge
        device_count = len(_connected_devices)
        if device_count > 0:
            with ui.row().classes("items-center q-gutter-xs"):
                ui.icon("link").style(f"color: {COLORS.green}; font-size: 1rem;")
                ui.label(f"{device_count} connected").classes("text-caption").style(
                    f"color: {COLORS.green};"
                )
        else:
            with ui.row().classes("items-center q-gutter-xs"):
                ui.icon("link_off").style(f"color: {COLORS.text_muted}; font-size: 1rem;")
                ui.label("No devices").classes("text-caption").style(
                    f"color: {COLORS.text_muted};"
                )
