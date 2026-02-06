"""
Device info card for the discovery list.

Shows device address, IDs, firmware version, max speed, and connect button.
"""

import functools

from nicegui import ui

from phoenix.models.device_info import DeviceInfo
from phoenix.ui.theme import COLORS


def render_device_card(
    device_info: DeviceInfo,
    on_connect,
    is_connected: bool = False,
) -> None:
    """Render a card for a discovered device.

    Args:
        device_info: Device information from discovery.
        on_connect: Async callback(handle) when connect button is clicked.
        is_connected: Whether this device is already connected.
    """
    with ui.card().classes("w-full q-pa-md"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("q-gutter-xs"):
                with ui.row().classes("items-center q-gutter-sm"):
                    ui.icon("memory").style(
                        f"color: {COLORS.cyan}; font-size: 1.5rem;"
                    )
                    ui.label(
                        f"BCM85667 @ 0x{device_info.device_address:02X}"
                    ).classes("text-h6").style(f"color: {COLORS.text_primary};")

                with ui.row().classes("q-gutter-md"):
                    _info_chip("Vendor", device_info.vendor_id_str)
                    _info_chip("Device", device_info.device_id_str)
                    _info_chip("Rev", str(device_info.revision_id))
                    _info_chip("FW", device_info.firmware_version_str)
                    _info_chip("Max", device_info.max_speed.name)

            if is_connected:
                ui.button(
                    "Connected", icon="check_circle",
                ).props("flat color=positive disable")
            else:
                # Use functools.partial to avoid lambda-wrapping an async callback
                ui.button(
                    "Connect", icon="link",
                    on_click=functools.partial(on_connect, device_info.product_handle),
                ).props("color=primary")


def _info_chip(label: str, value: str) -> None:
    """Render a small label+value chip."""
    with ui.row().classes("items-center q-gutter-xs"):
        ui.label(label).classes("text-caption").style(
            f"color: {COLORS.text_muted};"
        )
        ui.label(value).classes("text-caption hex-value")
