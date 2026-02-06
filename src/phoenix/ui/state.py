"""
Session state management for the Phoenix dashboard.

Uses a simple module-level dict keyed by NiceGUI client ID.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from phoenix.models.status import RetimerStatus


@dataclass
class UIState:
    """Per-session UI state tracked across page navigations."""

    connected_handle: Optional[int] = None
    last_status: Optional[RetimerStatus] = None
    auto_refresh: bool = True
    refresh_interval_s: float = 2.0
    sidebar_expanded: bool = True

    # Discovery form defaults
    transport_type: str = "i2c"
    i2c_port: int = 0
    i2c_speed: int = 400
    i2c_addresses: str = "0x50"
    uart_port: str = ""
    uart_baud: int = 115200


# Module-level session storage (simple, no serialization needed)
_sessions: Dict[str, UIState] = {}


def get_ui_state(client_id: str = "default") -> UIState:
    """Get or create UI state for a given session.

    Args:
        client_id: Session identifier. Defaults to "default" for single-user.

    Returns:
        UIState instance for this session.
    """
    if client_id not in _sessions:
        _sessions[client_id] = UIState()
    return _sessions[client_id]
