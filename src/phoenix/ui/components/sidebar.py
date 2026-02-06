"""
Navigation sidebar with device tree.

Shows discovered/connected devices and page navigation links.
"""

from typing import Optional

from nicegui import ui

from phoenix.api.app import _connected_devices
from phoenix.ui.theme import COLORS


def render_sidebar(
    current_handle: Optional[int] = None,
    current_path: str = "/",
) -> None:
    """Render the navigation sidebar.

    Args:
        current_handle: Currently viewed device handle, if any.
        current_path: Current page path for active link highlighting.
    """
    with ui.column().classes("w-full q-pa-sm q-gutter-sm"):
        # Discovery link
        _nav_item(
            "Device Discovery", "search", "/",
            active=(current_path == "/"),
        )

        ui.separator().style(f"background-color: {COLORS.border};")

        # Connected devices section
        ui.label("CONNECTED DEVICES").classes("section-title q-px-sm q-pt-sm")

        if not _connected_devices:
            ui.label("No devices connected").classes("text-caption q-px-sm").style(
                f"color: {COLORS.text_muted};"
            )
        else:
            for handle, device in _connected_devices.items():
                is_active = handle == current_handle
                addr = f"0x{device.device_info.device_address:02X}"
                fw = device.device_info.firmware_version_str

                with ui.expansion(
                    text=f"Device {addr}",
                    icon="memory",
                    value=is_active,
                ).classes("w-full").style(
                    f"color: {COLORS.text_primary};"
                ):
                    ui.label(f"FW {fw}").classes("text-caption q-pl-lg").style(
                        f"color: {COLORS.text_secondary};"
                    )

                    dash_path = f"/device/{handle}"
                    _nav_item(
                        "Dashboard", "dashboard",
                        dash_path,
                        active=(current_path == dash_path),
                        indent=True,
                    )

                    ports_path = f"/device/{handle}/ports"
                    _nav_item(
                        "Ports", "settings_ethernet",
                        ports_path,
                        active=(current_path == ports_path),
                        indent=True,
                    )

                    config_path = f"/device/{handle}/config"
                    _nav_item(
                        "Configuration", "tune",
                        config_path,
                        active=(current_path == config_path),
                        indent=True,
                    )

                    diag_path = f"/device/{handle}/diagnostics"
                    _nav_item(
                        "Diagnostics", "science",
                        diag_path,
                        active=(current_path == diag_path),
                        indent=True,
                    )

                    reg_path = f"/device/{handle}/registers"
                    _nav_item(
                        "Registers", "grid_on",
                        reg_path,
                        active=(current_path == reg_path),
                        indent=True,
                    )


def _nav_item(
    label: str,
    icon: str,
    href: str,
    active: bool = False,
    indent: bool = False,
) -> None:
    """Render a single navigation item."""
    bg = COLORS.bg_elevated if active else "transparent"
    text_color = COLORS.cyan if active else COLORS.text_primary
    pad = "q-pl-lg" if indent else ""

    with ui.link(target=href).classes(f"no-decoration w-full {pad}"):
        with ui.row().classes("items-center q-pa-sm q-gutter-sm rounded").style(
            f"background-color: {bg}; width: 100%;"
        ):
            ui.icon(icon).style(f"color: {text_color}; font-size: 1.1rem;")
            ui.label(label).style(f"color: {text_color}; font-size: 0.85rem;")
