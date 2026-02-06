"""
16-lane grid component with color-coded per-lane status.
"""

from typing import List

from nicegui import ui

from phoenix.models.status import LaneStatus
from phoenix.ui.theme import COLORS


def render_lane_grid(lane_statuses: List[LaneStatus]) -> None:
    """Render a 16-lane visual grid.

    Each lane is a small colored cell showing RX detect and EQ status.

    Args:
        lane_statuses: List of per-lane status models.
    """
    ui.label("LANE STATUS").classes("section-title")

    with ui.grid(columns=8).classes("q-gutter-xs"):
        for i in range(16):
            lane = _find_lane(lane_statuses, i)
            _render_lane_cell(i, lane)


def _find_lane(lanes: List[LaneStatus], lane_number: int):
    """Find lane status by number, returning None if not found."""
    for lane in lanes:
        if lane.lane_number == lane_number:
            return lane
    return None


def _render_lane_cell(lane_number: int, lane: LaneStatus = None) -> None:
    """Render a single lane cell."""
    if lane is None:
        color = COLORS.text_muted
        bg = COLORS.bg_elevated
    elif lane.rx_detect and lane.tx_eq_done and lane.rx_eq_done:
        color = COLORS.green
        bg = COLORS.green_dim
    elif lane.rx_detect:
        color = COLORS.yellow
        bg = COLORS.yellow_dim
    else:
        color = COLORS.text_muted
        bg = COLORS.bg_elevated

    tooltip_parts = [f"Lane {lane_number}"]
    if lane is not None:
        tooltip_parts.append(f"RX Detect: {'Yes' if lane.rx_detect else 'No'}")
        tooltip_parts.append(f"TX EQ: {'Done' if lane.tx_eq_done else 'Pending'}")
        tooltip_parts.append(f"RX EQ: {'Done' if lane.rx_eq_done else 'Pending'}")
    tooltip_text = "\n".join(tooltip_parts)

    with ui.element("div").style(
        f"width: 36px; height: 36px; border-radius: 4px; "
        f"background-color: {bg}; border: 1px solid {color}; "
        f"display: flex; align-items: center; justify-content: center; "
        f"cursor: default;"
    ).tooltip(tooltip_text):
        ui.label(str(lane_number)).style(
            f"color: {color}; font-size: 0.7rem; font-weight: 600;"
        )
