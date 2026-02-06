"""
Diagnostics page with tabbed PRBS, Eye Diagram, ELA, BELA, and LinkCAT tools.

Route: /device/{handle}/diagnostics
"""

from nicegui import ui

from phoenix.api.app import get_device
from phoenix.protocol.enums import PRBSPattern, MaxDataRate
from phoenix.ui.layout import page_layout
from phoenix.ui.theme import COLORS


def diagnostics_page(handle: int) -> None:
    """Render the diagnostics page with tabbed tools."""

    def build_content():
        ui.label("Diagnostics").classes("text-h5 q-mb-md").style(
            f"color: {COLORS.text_primary};"
        )

        with ui.tabs().classes("w-full").props(
            f"active-color=cyan indicator-color=cyan"
        ) as tabs:
            prbs_tab = ui.tab("PRBS", icon="speed")
            eye_tab = ui.tab("Eye Diagram", icon="visibility")
            ela_tab = ui.tab("ELA", icon="analytics")
            bela_tab = ui.tab("BELA", icon="bug_report")
            linkcat_tab = ui.tab("LinkCAT", icon="cable")

        with ui.tab_panels(tabs, value=prbs_tab).classes("w-full"):
            with ui.tab_panel(prbs_tab):
                _build_prbs_panel(handle)
            with ui.tab_panel(eye_tab):
                _build_eye_panel(handle)
            with ui.tab_panel(ela_tab):
                _build_ela_panel(handle)
            with ui.tab_panel(bela_tab):
                _build_bela_panel(handle)
            with ui.tab_panel(linkcat_tab):
                _build_linkcat_panel(handle)

    page_layout(
        title="Diagnostics",
        handle=handle,
        content_builder=build_content,
    )


def _build_prbs_panel(handle: int) -> None:
    """Build PRBS test controls and results."""
    results_container = None
    status_label = None

    with ui.card().classes("w-full q-pa-md"):
        ui.label("PRBS TEST CONFIGURATION").classes("section-title")

        with ui.row().classes("w-full q-gutter-md"):
            pattern_opts = {p.value: p.name for p in PRBSPattern}
            pattern_select = ui.select(
                pattern_opts,
                label="Pattern",
                value=PRBSPattern.PRBS31.value,
            ).classes("col")

            rate_opts = {
                r.value: f"{r.name} ({r.speed_gt_s} GT/s)"
                for r in MaxDataRate if r != MaxDataRate.RESERVED
            }
            rate_select = ui.select(
                rate_opts,
                label="Data Rate",
                value=MaxDataRate.GEN5_32G.value,
            ).classes("col")

        # Lane selection
        ui.label("Lanes").classes("text-caption q-mt-md").style(
            f"color: {COLORS.text_secondary};"
        )
        lane_checks = []
        with ui.row().classes("q-gutter-xs"):
            for i in range(16):
                cb = ui.checkbox(str(i), value=True).props("dense")
                lane_checks.append(cb)

        sample_count = ui.number(
            "Sample Count (hex)",
            value=0x100000,
        ).classes("q-mt-md")

        with ui.row().classes("q-mt-md q-gutter-sm"):
            start_btn = ui.button("Start PRBS", icon="play_arrow").props("color=primary")
            stop_btn = ui.button("Stop PRBS", icon="stop").props("color=negative outline")
            status_btn = ui.button("Get Results", icon="assessment").props("color=secondary outline")

        status_label = ui.label("").classes("text-caption q-mt-sm").style(
            f"color: {COLORS.text_secondary};"
        )

    results_container = ui.column().classes("w-full q-mt-md")

    async def start_prbs():
        start_btn.props("loading")
        status_label.text = "Starting PRBS test..."
        try:
            device = get_device(handle)
            lanes = [i for i, cb in enumerate(lane_checks) if cb.value]
            pattern = PRBSPattern(pattern_select.value)
            data_rate = MaxDataRate(rate_select.value)

            from phoenix.models.diagnostics import PRBSConfig
            config = PRBSConfig(
                pattern=pattern,
                data_rate=data_rate,
                lanes=lanes,
                generator_enable=True,
                checker_enable=True,
                sample_count=int(sample_count.value),
            )
            # The device API starts the PRBS test
            # This is a direct call -- not via REST
            await device.start_prbs(config)
            status_label.text = "PRBS test running..."
            status_label.style(f"color: {COLORS.green};")
        except Exception as e:
            status_label.text = f"Failed to start: {e}"
            status_label.style(f"color: {COLORS.red};")
        finally:
            start_btn.props(remove="loading")

    async def stop_prbs():
        try:
            device = get_device(handle)
            await device.stop_prbs()
            status_label.text = "PRBS test stopped."
        except Exception as e:
            status_label.text = f"Failed to stop: {e}"
            status_label.style(f"color: {COLORS.red};")

    async def get_results():
        status_btn.props("loading")
        try:
            device = get_device(handle)
            results = await device.get_prbs_results()

            results_container.clear()
            with results_container:
                ui.label("PRBS RESULTS").classes("section-title")

                columns = [
                    {"name": "lane", "label": "Lane", "field": "lane", "align": "center"},
                    {"name": "bits", "label": "Bit Count", "field": "bits", "align": "right"},
                    {"name": "errors", "label": "Errors", "field": "errors", "align": "right"},
                    {"name": "ber", "label": "BER", "field": "ber", "align": "right"},
                    {"name": "sync", "label": "Sync", "field": "sync", "align": "center"},
                    {"name": "done", "label": "Complete", "field": "done", "align": "center"},
                ]

                rows = []
                for r in results:
                    rows.append({
                        "lane": r.lane_number,
                        "bits": f"{r.bit_count:,}",
                        "errors": f"{r.error_count:,}",
                        "ber": r.ber_string,
                        "sync": "Yes" if r.sync_acquired else "No",
                        "done": "Yes" if r.test_complete else "No",
                    })

                ui.table(
                    columns=columns, rows=rows, row_key="lane",
                ).classes("w-full").props("dense flat bordered")

            status_label.text = f"Retrieved results for {len(results)} lane(s)."

        except Exception as e:
            status_label.text = f"Failed to get results: {e}"
            status_label.style(f"color: {COLORS.red};")
        finally:
            status_btn.props(remove="loading")

    start_btn.on_click(start_prbs)
    stop_btn.on_click(stop_prbs)
    status_btn.on_click(get_results)


def _build_eye_panel(handle: int) -> None:
    """Build Eye Diagram capture controls."""
    results_container = None
    status_label = None

    with ui.card().classes("w-full q-pa-md"):
        ui.label("EYE DIAGRAM CAPTURE").classes("section-title")

        with ui.row().classes("q-gutter-md"):
            lane_select = ui.number("Lane", value=0, min=0, max=15).classes("col-3")
            rate_opts = {
                r.value: f"{r.name} ({r.speed_gt_s} GT/s)"
                for r in MaxDataRate if r != MaxDataRate.RESERVED
            }
            rate_select = ui.select(
                rate_opts,
                label="Data Rate",
                value=MaxDataRate.GEN5_32G.value,
            ).classes("col")

        capture_btn = ui.button("Capture Eye", icon="visibility").props("color=primary q-mt-md")

        status_label = ui.label("").classes("text-caption q-mt-sm").style(
            f"color: {COLORS.text_secondary};"
        )

    results_container = ui.column().classes("w-full q-mt-md")

    async def capture_eye():
        capture_btn.props("loading")
        status_label.text = "Capturing eye diagram..."
        try:
            device = get_device(handle)
            from phoenix.models.diagnostics import EyeDiagramResult
            result = await device.capture_eye_diagram(
                lane=int(lane_select.value),
                data_rate=MaxDataRate(rate_select.value),
            )

            results_container.clear()
            with results_container:
                _render_eye_result(result)

            status_label.text = "Eye diagram captured."
            status_label.style(f"color: {COLORS.green};")

        except Exception as e:
            status_label.text = f"Capture failed: {e}"
            status_label.style(f"color: {COLORS.red};")
        finally:
            capture_btn.props(remove="loading")

    capture_btn.on_click(capture_eye)


def _render_eye_result(result) -> None:
    """Render eye diagram results as margin display."""
    with ui.card().classes("w-full q-pa-md"):
        ui.label(f"EYE DIAGRAM - LANE {result.lane_number}").classes("section-title")

        valid_color = COLORS.green if result.capture_valid else COLORS.red
        ui.label(
            f"Capture {'Valid' if result.capture_valid else 'Invalid'}"
        ).style(f"color: {valid_color};")

        if result.middle_eye:
            ui.label("Middle Eye").classes("text-subtitle2 q-mt-md").style(
                f"color: {COLORS.text_secondary};"
            )
            _eye_margin_display(result.middle_eye)

        if result.lower_eye:
            ui.label("Lower Eye (Gen6)").classes("text-subtitle2 q-mt-md").style(
                f"color: {COLORS.text_secondary};"
            )
            _eye_margin_display(result.lower_eye)

        if result.upper_eye:
            ui.label("Upper Eye (Gen6)").classes("text-subtitle2 q-mt-md").style(
                f"color: {COLORS.text_secondary};"
            )
            _eye_margin_display(result.upper_eye)


def _eye_margin_display(margin) -> None:
    """Render eye margin values."""
    with ui.grid(columns=2).classes("q-gutter-sm"):
        _margin_stat("Left Margin", f"{margin.left_margin_mui} mUI")
        _margin_stat("Right Margin", f"{margin.right_margin_mui} mUI")
        _margin_stat("Upper Margin", f"{margin.upper_margin_mv} mV")
        _margin_stat("Lower Margin", f"{margin.lower_margin_mv} mV")
        _margin_stat("H Opening", f"{margin.horizontal_opening_mui} mUI")
        _margin_stat("V Opening", f"{margin.vertical_opening_mv} mV")


def _margin_stat(label: str, value: str) -> None:
    """Render a margin stat pair."""
    ui.label(label).classes("text-caption").style(f"color: {COLORS.text_muted};")
    ui.label(value).classes("mono").style(f"color: {COLORS.cyan};")


def _build_ela_panel(handle: int) -> None:
    """Build ELA (Embedded Logic Analyzer) controls."""
    with ui.card().classes("w-full q-pa-md"):
        ui.label("EMBEDDED LOGIC ANALYZER (ELA)").classes("section-title")
        ui.label(
            "Configure and capture ELA traces for protocol-level debugging. "
            "Supports up to 8 trigger signals with rising, falling, or pattern match."
        ).classes("text-body2 q-mb-md").style(f"color: {COLORS.text_secondary};")

        from phoenix.protocol.enums import ELAType, ELATriggerPosition

        with ui.row().classes("q-gutter-md"):
            ui.select(
                {t.value: t.name for t in ELAType},
                label="ELA Type",
                value=ELAType.PSEUDO_PORT_A.value,
            ).classes("col")
            ui.select(
                {p.value: p.name for p in ELATriggerPosition},
                label="Trigger Position",
                value=ELATriggerPosition.POS_50.value,
            ).classes("col")

        ui.switch("Mixed Mode (AND triggers)").classes("q-mt-md")

        with ui.row().classes("q-mt-md q-gutter-sm"):
            ui.button("Configure", icon="settings").props("color=primary disable").tooltip(
                "Not yet implemented"
            )
            ui.button("Start Capture", icon="play_arrow").props("color=positive outline disable").tooltip(
                "Not yet implemented"
            )
            ui.button("Read Results", icon="download").props("color=secondary outline disable").tooltip(
                "Not yet implemented"
            )

        ui.label(
            "ELA configuration and capture require firmware support. Controls not yet implemented."
        ).classes("text-caption q-mt-md").style(f"color: {COLORS.text_muted};")


def _build_bela_panel(handle: int) -> None:
    """Build BELA (Broadcom Embedded Logic Analyzer) controls."""
    with ui.card().classes("w-full q-pa-md"):
        ui.label("BROADCOM EMBEDDED LOGIC ANALYZER (BELA)").classes("section-title")
        ui.label(
            "Lane-level logic analyzer for capturing PHY-layer signal transitions. "
            "Monitors a single lane with configurable trigger conditions."
        ).classes("text-body2 q-mb-md").style(f"color: {COLORS.text_secondary};")

        from phoenix.protocol.enums import BELATriggerType

        with ui.row().classes("q-gutter-md"):
            ui.number("Lane", value=0, min=0, max=15).classes("col-2")
            rate_opts = {
                r.value: f"{r.name}"
                for r in MaxDataRate if r != MaxDataRate.RESERVED
            }
            ui.select(
                rate_opts,
                label="Trigger Rate",
                value=MaxDataRate.GEN5_32G.value,
            ).classes("col")
            ui.select(
                {t.value: t.name for t in BELATriggerType},
                label="Trigger Type",
                value=BELATriggerType.LIVE_DATARATE.value,
            ).classes("col")

        with ui.row().classes("q-mt-md q-gutter-md"):
            ui.switch("Force Capture")
            ui.switch("Auto Restart")

        with ui.row().classes("q-mt-md q-gutter-sm"):
            ui.button("Start BELA", icon="play_arrow").props("color=primary disable").tooltip(
                "Not yet implemented"
            )
            ui.button("Stop BELA", icon="stop").props("color=negative outline disable").tooltip(
                "Not yet implemented"
            )
            ui.button("Get Status", icon="info").props("color=secondary outline disable").tooltip(
                "Not yet implemented"
            )

        ui.label(
            "BELA captures require firmware support and may impact link performance. "
            "Controls not yet implemented."
        ).classes("text-caption q-mt-md").style(f"color: {COLORS.text_muted};")


def _build_linkcat_panel(handle: int) -> None:
    """Build LinkCAT (Link Channel Analysis Tool) controls."""
    with ui.card().classes("w-full q-pa-md"):
        ui.label("LINK CHANNEL ANALYSIS TOOL (LinkCAT)").classes("section-title")
        ui.label(
            "Characterize the PCIe channel by measuring insertion loss at symbol rate. "
            "Supports LP TX, Loopback, Pre-RX, and RX Measure modes."
        ).classes("text-body2 q-mb-md").style(f"color: {COLORS.text_secondary};")

        from phoenix.protocol.enums import LinkCATMode

        with ui.row().classes("q-gutter-md"):
            ui.select(
                {m.value: m.name for m in LinkCATMode},
                label="Mode",
                value=LinkCATMode.LP_TX.value,
            ).classes("col")
            ui.number(
                "TX Amplitude Scale (0=default)",
                value=0, min=0, max=99,
            ).classes("col")

        with ui.row().classes("q-mt-md q-gutter-sm"):
            ui.button("Run LinkCAT", icon="cable").props("color=primary disable").tooltip(
                "Not yet implemented"
            )
            ui.button("Get Results", icon="assessment").props("color=secondary outline disable").tooltip(
                "Not yet implemented"
            )

        ui.label(
            "LinkCAT requires the link to be in a specific state. "
            "Ensure proper setup before running. Controls not yet implemented."
        ).classes("text-caption q-mt-md").style(f"color: {COLORS.text_muted};")
