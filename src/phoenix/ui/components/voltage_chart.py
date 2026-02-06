"""
ECharts bar chart for voltage rail display (7 rails).
"""

from nicegui import ui

from phoenix.models.status import VoltageInfo
from phoenix.ui.theme import COLORS


RAIL_NAMES = ["DVDD1", "DVDD2", "DVDD3", "DVDD4", "DVDD5", "DVDD6", "DVDDIO"]


def render_voltage_chart(voltage: VoltageInfo = None) -> ui.echart:
    """Render a voltage bar chart using ECharts.

    Args:
        voltage: Voltage info model. None for empty chart.

    Returns:
        The ECharts element for later updates.
    """
    values = _extract_values(voltage)
    chart = ui.echart(_chart_options(values)).classes("w-full").style(
        "height: 200px;"
    )
    return chart


def update_voltage_chart(chart: ui.echart, voltage: VoltageInfo) -> None:
    """Update an existing voltage chart with new values."""
    values = _extract_values(voltage)
    chart.options = _chart_options(values)
    chart.update()


def _extract_values(voltage: VoltageInfo = None) -> list[int]:
    """Extract voltage values from model into ordered list."""
    if voltage is None:
        return [0] * 7
    return [
        voltage.dvdd1_mv,
        voltage.dvdd2_mv,
        voltage.dvdd3_mv,
        voltage.dvdd4_mv,
        voltage.dvdd5_mv,
        voltage.dvdd6_mv,
        voltage.dvddio_mv,
    ]


def _chart_options(values: list[int]) -> dict:
    """Build ECharts bar chart option dict."""
    return {
        "tooltip": {
            "trigger": "axis",
            "formatter": "{b}: {c} mV",
            "backgroundColor": COLORS.bg_elevated,
            "borderColor": COLORS.border,
            "textStyle": {"color": COLORS.text_primary},
        },
        "grid": {
            "left": "12%",
            "right": "5%",
            "top": "8%",
            "bottom": "15%",
        },
        "xAxis": {
            "type": "category",
            "data": RAIL_NAMES,
            "axisLabel": {
                "color": COLORS.text_secondary,
                "fontSize": 10,
                "rotate": 0,
            },
            "axisLine": {"lineStyle": {"color": COLORS.border}},
        },
        "yAxis": {
            "type": "value",
            "name": "mV",
            "nameTextStyle": {"color": COLORS.text_muted, "fontSize": 10},
            "axisLabel": {"color": COLORS.text_secondary, "fontSize": 10},
            "axisLine": {"lineStyle": {"color": COLORS.border}},
            "splitLine": {"lineStyle": {"color": COLORS.border, "type": "dashed"}},
        },
        "series": [
            {
                "type": "bar",
                "data": values,
                "barWidth": "50%",
                "itemStyle": {
                    "color": COLORS.blue,
                    "borderRadius": [3, 3, 0, 0],
                },
                "label": {
                    "show": True,
                    "position": "top",
                    "color": COLORS.text_secondary,
                    "fontSize": 10,
                    "formatter": "{c}",
                },
            }
        ],
    }
