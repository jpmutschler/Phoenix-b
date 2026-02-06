"""
Status indicator components: colored dots, badges, and labels.
"""

from nicegui import ui

from phoenix.ui.theme import COLORS


def status_dot(color: str, size: str = "10px") -> ui.html:
    """Render a colored status dot.

    Args:
        color: CSS color string.
        size: Dot diameter.
    """
    return ui.html(
        f'<span style="display:inline-block; width:{size}; height:{size}; '
        f'border-radius:50%; background-color:{color};"></span>'
    )


def status_badge(text: str, color: str) -> None:
    """Render a status badge with colored background.

    Args:
        text: Badge text.
        color: Status color.
    """
    dim_colors = {
        COLORS.green: COLORS.green_dim,
        COLORS.yellow: COLORS.yellow_dim,
        COLORS.red: COLORS.red_dim,
    }
    bg = dim_colors.get(color, COLORS.bg_elevated)

    ui.label(text).classes("text-caption q-px-sm q-py-xs rounded").style(
        f"color: {color}; background-color: {bg}; "
        f"border: 1px solid {color}; font-weight: 600;"
    )


def link_status_badge(is_up: bool) -> None:
    """Render a link up/down badge."""
    if is_up:
        status_badge("LINK UP", COLORS.green)
    else:
        status_badge("LINK DOWN", COLORS.text_muted)


def health_badge(is_healthy: bool) -> None:
    """Render a health status badge."""
    if is_healthy:
        status_badge("HEALTHY", COLORS.green)
    else:
        status_badge("UNHEALTHY", COLORS.red)
