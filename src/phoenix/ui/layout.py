"""
Shared page layout with header, sidebar, and content area.

Every page uses page_layout() to get consistent nav and structure.
"""

from typing import Callable, Optional

from nicegui import ui

from phoenix.ui.theme import COLORS, GLOBAL_CSS
from phoenix.ui.components.header import render_header
from phoenix.ui.components.sidebar import render_sidebar


def page_layout(
    title: str,
    handle: Optional[int] = None,
    content_builder: Optional[Callable] = None,
    current_path: Optional[str] = None,
) -> None:
    """Render the shared page layout with header, sidebar, and content area.

    Args:
        title: Page title shown in header.
        handle: Device handle if a device page. None for discovery page.
        content_builder: Callable that builds the main content area.
        current_path: Current page path for sidebar active highlighting.
    """
    # Infer path from title if not provided
    if current_path is None and handle is not None:
        path_map = {
            "Dashboard": f"/device/{handle}",
            "Port Status": f"/device/{handle}/ports",
            "Configuration": f"/device/{handle}/config",
            "Diagnostics": f"/device/{handle}/diagnostics",
            "Register Browser": f"/device/{handle}/registers",
        }
        current_path = path_map.get(title, f"/device/{handle}")
    elif current_path is None:
        current_path = "/"

    ui.add_css(GLOBAL_CSS)

    ui.dark_mode(True)
    ui.colors(primary=COLORS.cyan, secondary=COLORS.blue, accent=COLORS.purple)

    with ui.header(elevated=True).classes("q-pa-sm"):
        render_header(title, handle)

    with ui.left_drawer(value=True, bordered=True).classes("q-pa-none").style(
        f"width: 240px; background-color: {COLORS.bg_secondary};"
    ) as drawer:
        render_sidebar(handle, current_path)

    if content_builder is not None:
        with ui.column().classes("q-pa-md w-full").style(
            f"background-color: {COLORS.bg_primary};"
        ):
            content_builder()
