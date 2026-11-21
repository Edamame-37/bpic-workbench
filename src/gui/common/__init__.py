"""Reusable GUI components shared by feature panels."""

"""Shared GUI components."""

from src.gui.common.navigation import (
    NAVIGATION_ROUTES,
    ROUTES_BY_ID,
    NavigationRoute,
    NavigationSidebar,
)
from src.gui.common.status_banner import StatusBanner
from src.gui.common.workspace_chrome import GlobalActionBar, WorkspaceHeader

__all__ = [
    "GlobalActionBar",
    "NAVIGATION_ROUTES",
    "NavigationRoute",
    "NavigationSidebar",
    "ROUTES_BY_ID",
    "StatusBanner",
    "WorkspaceHeader",
]
