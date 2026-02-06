"""
Page route registration and NiceGUI integration.

Provides setup_ui(app) which mounts NiceGUI onto the existing FastAPI app
via ui.run_with(app). REST API continues to work at /api/.
"""

import os
import secrets

from fastapi import FastAPI
from nicegui import app as nicegui_app, ui

from phoenix.ui.pages.discovery import discovery_page
from phoenix.ui.pages.dashboard import dashboard_page
from phoenix.ui.pages.ports import ports_page
from phoenix.ui.pages.configuration import configuration_page
from phoenix.ui.pages.diagnostics import diagnostics_page
from phoenix.ui.pages.registers import registers_page


def setup_ui(app: FastAPI) -> None:
    """Mount NiceGUI dashboard onto the existing FastAPI application.

    Registers all UI page routes and starts NiceGUI with ui.run_with(app).
    The REST API at /api/ continues working alongside the UI.

    Args:
        app: The FastAPI application instance to mount onto.
    """
    storage_secret = os.environ.get("PHOENIX_STORAGE_SECRET")
    if not storage_secret:
        storage_secret = secrets.token_urlsafe(32)

    _register_pages()
    ui.run_with(
        app,
        title="Phoenix Retimer Dashboard",
        favicon="🔌",
        dark=True,
        storage_secret=storage_secret,
    )


def _register_pages() -> None:
    """Register all page routes with NiceGUI."""

    @ui.page("/")
    def _discovery():
        discovery_page()

    @ui.page("/device/{handle}")
    def _dashboard(handle: int):
        dashboard_page(handle)

    @ui.page("/device/{handle}/ports")
    def _ports(handle: int):
        ports_page(handle)

    @ui.page("/device/{handle}/config")
    def _config(handle: int):
        configuration_page(handle)

    @ui.page("/device/{handle}/diagnostics")
    def _diagnostics(handle: int):
        diagnostics_page(handle)

    @ui.page("/device/{handle}/registers")
    def _registers(handle: int):
        registers_page(handle)
