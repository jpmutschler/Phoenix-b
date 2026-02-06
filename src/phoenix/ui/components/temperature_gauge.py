"""
ECharts circular gauge for temperature display (0-125 C).

Color bands: green (0-85), yellow (85-100), red (100-125).
"""

from nicegui import ui

from phoenix.ui.theme import COLORS, THRESHOLDS


def render_temperature_gauge(temperature_c: int = 0) -> ui.echart:
    """Render a temperature gauge using ECharts.

    Args:
        temperature_c: Current temperature in degrees Celsius.

    Returns:
        The ECharts element for later updates.
    """
    chart = ui.echart(_gauge_options(temperature_c)).classes("w-full").style(
        "height: 220px;"
    )
    return chart


def update_temperature_gauge(chart: ui.echart, temperature_c: int) -> None:
    """Update an existing temperature gauge with new value."""
    chart.options = _gauge_options(temperature_c)
    chart.update()


def _gauge_options(temperature_c: int) -> dict:
    """Build ECharts gauge option dict."""
    return {
        "series": [
            {
                "type": "gauge",
                "min": 0,
                "max": THRESHOLDS.temp_critical_max,
                "startAngle": 220,
                "endAngle": -40,
                "splitNumber": 5,
                "axisLine": {
                    "lineStyle": {
                        "width": 12,
                        "color": [
                            [THRESHOLDS.temp_normal_max / THRESHOLDS.temp_critical_max,
                             COLORS.green],
                            [THRESHOLDS.temp_warning_max / THRESHOLDS.temp_critical_max,
                             COLORS.yellow],
                            [1.0, COLORS.red],
                        ],
                    },
                },
                "axisTick": {
                    "length": 6,
                    "lineStyle": {"color": COLORS.text_muted},
                },
                "splitLine": {
                    "length": 12,
                    "lineStyle": {"color": COLORS.text_muted, "width": 2},
                },
                "axisLabel": {
                    "distance": 18,
                    "color": COLORS.text_secondary,
                    "fontSize": 10,
                    "formatter": "{value}",
                },
                "pointer": {
                    "width": 4,
                    "length": "65%",
                    "itemStyle": {"color": COLORS.text_primary},
                },
                "anchor": {
                    "show": True,
                    "size": 8,
                    "itemStyle": {"color": COLORS.cyan},
                },
                "title": {
                    "show": True,
                    "offsetCenter": [0, "70%"],
                    "fontSize": 12,
                    "color": COLORS.text_secondary,
                },
                "detail": {
                    "valueAnimation": True,
                    "fontSize": 28,
                    "fontWeight": "bold",
                    "offsetCenter": [0, "45%"],
                    "formatter": "{value}°C",
                    "color": COLORS.text_primary,
                },
                "data": [{"value": temperature_c, "name": "Temperature"}],
            }
        ],
    }
