"""
Configuration editor page.

Route: /device/{handle}/config
Supports bifurcation, data rates, clocking modes, interrupts, TX coefficients, resets.
"""

from nicegui import ui

from phoenix.api.app import get_device
from phoenix.models.configuration import ConfigurationUpdate
from phoenix.protocol.enums import (
    BifurcationMode,
    ClockingMode,
    MaxDataRate,
    PortOrientation,
    ResetType,
)
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS


def configuration_page(handle: int) -> None:
    """Render the configuration editor page."""

    # References for reactive widgets
    bif_select = None
    rate_select = None
    clock_select = None
    orient_select = None
    intr_global = None
    intr_eq = None
    intr_phy = None
    intr_internal = None
    status_label = None
    error_label = None

    def build_content():
        nonlocal bif_select, rate_select, clock_select, orient_select
        nonlocal intr_global, intr_eq, intr_phy, intr_internal
        nonlocal status_label, error_label

        error_label = ui.label("").style(f"color: {COLORS.red};")
        error_label.visible = False

        ui.label("Device Configuration").classes("text-h5 q-mb-md").style(
            f"color: {COLORS.text_primary};"
        )

        # Main config card
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            ui.label("LINK CONFIGURATION").classes("section-title")

            with ui.grid(columns=2).classes("w-full q-gutter-md"):
                bif_options = {m.value: m.name for m in BifurcationMode}
                bif_select = ui.select(
                    bif_options,
                    label="Bifurcation Mode",
                    value=BifurcationMode.X16.value,
                ).classes("w-full")

                rate_options = {
                    r.value: f"{r.name} ({r.speed_gt_s} GT/s)"
                    for r in MaxDataRate if r != MaxDataRate.RESERVED
                }
                rate_select = ui.select(
                    rate_options,
                    label="Max Data Rate",
                    value=MaxDataRate.GEN6_64G.value,
                ).classes("w-full")

                clock_options = {
                    c.value: c.name
                    for c in ClockingMode
                    if "RESERVED" not in c.name
                }
                clock_select = ui.select(
                    clock_options,
                    label="Clocking Mode",
                    value=ClockingMode.COMMON_WO_SSC.value,
                ).classes("w-full")

                orient_options = {o.value: o.name for o in PortOrientation}
                orient_select = ui.select(
                    orient_options,
                    label="Port Orientation",
                    value=PortOrientation.STATIC.value,
                ).classes("w-full")

        # Interrupt configuration
        with ui.card().classes("w-full q-pa-md q-mb-md"):
            ui.label("INTERRUPT ENABLES").classes("section-title")

            with ui.column().classes("q-gutter-sm"):
                intr_global = ui.switch("Global Interrupt Enable")
                intr_eq = ui.switch("EQ Phase Error Enable")
                intr_phy = ui.switch("PHY Phase Error Enable")
                intr_internal = ui.switch("Internal Error Enable")

        # Action buttons
        with ui.row().classes("q-gutter-md q-mb-md"):
            apply_btn = ui.button(
                "Apply Configuration", icon="save",
            ).props("color=primary")
            refresh_btn = ui.button(
                "Refresh", icon="refresh",
            ).props("color=secondary outline")

        status_label = ui.label("").classes("text-caption").style(
            f"color: {COLORS.text_secondary};"
        )

        # Reset section
        with ui.card().classes("w-full q-pa-md q-mt-lg"):
            ui.label("DEVICE RESET").classes("section-title")
            ui.label(
                "Reset the device. Soft reset preserves sticky registers."
            ).classes("text-caption q-mb-md").style(f"color: {COLORS.text_muted};")

            with ui.row().classes("q-gutter-sm"):
                for rt in ResetType:
                    color = "negative" if rt in (ResetType.HARD, ResetType.GLOBAL_SWRST) else "warning"
                    ui.button(
                        rt.name, icon="restart_alt",
                        on_click=lambda _, r=rt: do_reset(r),
                    ).props(f"color={color} outline size=sm")

        # Load current config on page load
        ui.timer(0.1, load_config, once=True)

        async def apply_config():
            apply_btn.props("loading")
            status_label.text = "Applying..."
            try:
                device = get_device(handle)
                update = ConfigurationUpdate(
                    bifurcation_mode=BifurcationMode(bif_select.value),
                    max_data_rate=MaxDataRate(rate_select.value),
                    clocking_mode=ClockingMode(clock_select.value),
                    port_orientation=PortOrientation(orient_select.value),
                )
                await device.set_configuration(update)
                status_label.text = "Configuration applied successfully."
                status_label.style(f"color: {COLORS.green};")
            except Exception as e:
                status_label.text = f"Failed to apply: {e}"
                status_label.style(f"color: {COLORS.red};")
            finally:
                apply_btn.props(remove="loading")

        apply_btn.on_click(apply_config)
        refresh_btn.on_click(load_config)

    async def load_config():
        try:
            device = get_device(handle)
            config = await device.get_configuration()

            bif_select.value = config.bifurcation_mode.value
            rate_select.value = config.max_data_rate.value
            clock_select.value = config.clocking_mode.value
            orient_select.value = config.port_orientation.value

            intr_global.value = config.interrupt_config.global_interrupt_enable
            intr_eq.value = config.interrupt_config.eq_phase_error_enable
            intr_phy.value = config.interrupt_config.phy_phase_error_enable
            intr_internal.value = config.interrupt_config.internal_error_enable

            error_label.visible = False
            status_label.text = "Configuration loaded."
            status_label.style(f"color: {COLORS.text_secondary};")

        except Exception as e:
            error_label.text = f"Failed to load config: {e}"
            error_label.visible = True

    async def do_reset(reset_type: ResetType):
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Confirm {reset_type.name} Reset?").classes("text-h6")
            ui.label(
                "This will reset the device. The connection may be lost."
            ).classes("text-body2 q-my-md")

            with ui.row().classes("w-full justify-end q-gutter-sm"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Reset", icon="restart_alt",
                    on_click=lambda: execute_reset(reset_type, dialog),
                ).props("color=negative")

        dialog.open()

    async def execute_reset(reset_type: ResetType, dialog):
        dialog.close()
        try:
            device = get_device(handle)
            await device.reset(reset_type)
            status_label.text = f"{reset_type.name} reset completed."
            status_label.style(f"color: {COLORS.green};")
        except Exception as e:
            status_label.text = f"Reset failed: {e}"
            status_label.style(f"color: {COLORS.red};")

    page_layout(
        title="Configuration",
        handle=handle,
        content_builder=build_content,
    )
