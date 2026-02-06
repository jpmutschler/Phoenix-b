"""
Discovery page -- landing page for device scan and connection.

Route: /
"""

from nicegui import ui

from phoenix.api.app import (
    get_discovery,
    register_device,
    _connected_devices,
)
from phoenix.core.device import RetimerDevice
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS
from phoenix.ui.components.device_card import render_device_card


def discovery_page() -> None:
    """Render the discovery page content."""

    # Shared mutable containers for reactive updates
    discovered_devices = []
    device_list_container = None
    status_label = None

    def build_content():
        nonlocal device_list_container, status_label

        ui.label("Device Discovery").classes("text-h5 q-mb-md").style(
            f"color: {COLORS.text_primary};"
        )
        ui.label(
            "Scan for retimer devices on I2C or UART bus."
        ).classes("text-body2 q-mb-lg").style(f"color: {COLORS.text_secondary};")

        # Transport selection
        with ui.card().classes("w-full q-pa-md q-mb-lg"):
            ui.label("SCAN SETTINGS").classes("section-title")

            transport = ui.toggle(
                {"i2c": "I2C / SMBus", "uart": "UART"},
                value="i2c",
            ).props("no-caps spread")

            # I2C settings
            with ui.column().classes("w-full q-gutter-sm q-mt-md").bind_visibility_from(
                transport, "value", value="i2c"
            ):
                with ui.row().classes("w-full q-gutter-md"):
                    i2c_port = ui.number(
                        "Adapter Port", value=0, min=0, max=7,
                    ).classes("col-3")
                    i2c_speed = ui.select(
                        {100: "100 kHz", 400: "400 kHz", 1000: "1 MHz"},
                        value=400, label="Bus Speed",
                    ).classes("col-3")
                    i2c_addresses = ui.input(
                        "Addresses (hex, comma-separated)",
                        value="0x50, 0x51, 0x52, 0x53",
                        placeholder="0x50, 0x51, 0x52",
                    ).classes("col")

            # UART settings
            with ui.column().classes("w-full q-gutter-sm q-mt-md").bind_visibility_from(
                transport, "value", value="uart"
            ):
                with ui.row().classes("w-full q-gutter-md"):
                    uart_port = ui.input(
                        "Serial Port", value="COM3",
                        placeholder="COM3 or /dev/ttyUSB0",
                    ).classes("col")
                    uart_baud = ui.select(
                        {9600: "9600", 115200: "115200", 230400: "230400"},
                        value=115200, label="Baud Rate",
                    ).classes("col-3")

            with ui.row().classes("q-mt-md q-gutter-sm"):
                scan_btn = ui.button(
                    "Scan for Devices", icon="search",
                ).props("color=primary")

                direct_btn = ui.button(
                    "Direct Connect", icon="link",
                ).props("color=secondary outline")

            status_label = ui.label("").classes("text-caption q-mt-sm").style(
                f"color: {COLORS.text_secondary};"
            )

        # Results section
        ui.label("DISCOVERED DEVICES").classes("section-title")
        device_list_container = ui.column().classes("w-full q-gutter-md")

        # Scan handler
        async def do_scan():
            scan_btn.props("loading")
            status_label.text = "Scanning..."
            discovered_devices.clear()
            device_list_container.clear()

            try:
                discovery = get_discovery()

                if transport.value == "i2c":
                    addr_strs = [
                        a.strip() for a in i2c_addresses.value.split(",") if a.strip()
                    ]
                    addresses = [
                        int(a, 16) if a.startswith("0x") else int(a)
                        for a in addr_strs
                    ]
                    devices = await discovery.discover_i2c(
                        adapter_port=int(i2c_port.value),
                        addresses=addresses,
                        bus_speed_khz=int(i2c_speed.value),
                    )
                else:
                    devices = await discovery.discover_uart(
                        port=uart_port.value,
                        baud_rate=int(uart_baud.value),
                    )

                discovered_devices.extend(devices)
                status_label.text = f"Found {len(devices)} device(s)"

                with device_list_container:
                    if not devices:
                        ui.label("No devices found. Check connections and try again.").style(
                            f"color: {COLORS.text_muted};"
                        )
                    else:
                        for dev in devices:
                            is_conn = dev.product_handle in _connected_devices
                            render_device_card(dev, on_connect=do_connect, is_connected=is_conn)

            except Exception as e:
                status_label.text = f"Scan failed: {e}"
                status_label.style(f"color: {COLORS.red};")
            finally:
                scan_btn.props(remove="loading")

        async def do_connect(handle: int):
            status_label.text = f"Connecting to device {handle}..."
            try:
                discovery = get_discovery()
                device_info = discovery.get_device_by_handle(handle)
                if device_info is None:
                    status_label.text = "Device not found in discovery cache."
                    return

                device = RetimerDevice(device_info=device_info)
                await device.connect()
                register_device(device)

                status_label.text = f"Connected to device {handle}"
                ui.navigate.to(f"/device/{handle}")

            except Exception as e:
                status_label.text = f"Connection failed: {e}"
                status_label.style(f"color: {COLORS.red};")

        async def do_direct_connect():
            direct_btn.props("loading")
            status_label.text = "Connecting directly..."
            try:
                if transport.value == "i2c":
                    addr_strs = [
                        a.strip() for a in i2c_addresses.value.split(",") if a.strip()
                    ]
                    if not addr_strs:
                        status_label.text = "Enter at least one I2C address."
                        status_label.style(f"color: {COLORS.yellow};")
                        return
                    address = int(addr_strs[0], 16) if addr_strs[0].startswith("0x") else int(addr_strs[0])
                    device = await RetimerDevice.from_i2c(
                        address=address,
                        adapter_port=int(i2c_port.value),
                        bus_speed_khz=int(i2c_speed.value),
                    )
                else:
                    device = await RetimerDevice.from_uart(
                        port=uart_port.value,
                        baud_rate=int(uart_baud.value),
                    )

                await device.connect()
                register_device(device)
                handle = device.device_info.product_handle

                status_label.text = f"Connected to device {handle}"
                ui.navigate.to(f"/device/{handle}")

            except Exception as e:
                status_label.text = f"Direct connect failed: {e}"
                status_label.style(f"color: {COLORS.red};")
            finally:
                direct_btn.props(remove="loading")

        scan_btn.on_click(do_scan)
        direct_btn.on_click(do_direct_connect)

    page_layout(title="Device Discovery", content_builder=build_content)
