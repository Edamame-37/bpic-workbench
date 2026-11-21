"""Persistent workspace navigation inspired by process-analysis tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class NavigationRoute:
    route_id: str
    title: str
    group: str
    shortcut: str
    description: str
    icon: QStyle.StandardPixmap


NAVIGATION_ROUTES: Final[tuple[NavigationRoute, ...]] = (
    NavigationRoute("dataset", "Dataset & Status", "WORKSPACE", "Ctrl+1", "Import dan validasi XES", QStyle.StandardPixmap.SP_DirOpenIcon),
    NavigationRoute("overview", "Overview", "WORKSPACE", "Ctrl+2", "KPI dan statistik log", QStyle.StandardPixmap.SP_FileDialogInfoView),
    NavigationRoute("exercise_11_7", "Exercise 11.7", "ANALYSES", "Ctrl+3", "Cycle time dan case outcomes", QStyle.StandardPixmap.SP_ComputerIcon),
    NavigationRoute("rework", "Rework 11.15 / 11.18", "ANALYSES", "Ctrl+4", "Repeated complete dan resource", QStyle.StandardPixmap.SP_BrowserReload),
    NavigationRoute("sequence", "Exercise 11.22", "ANALYSES", "Ctrl+5", "Eventually-follows evidence", QStyle.StandardPixmap.SP_ArrowForward),
    NavigationRoute("explorer", "Case Explorer", "INVESTIGATION", "Ctrl+6", "Trace lengkap dan evidence", QStyle.StandardPixmap.SP_FileDialogDetailedView),
    NavigationRoute("export", "Export", "OUTPUT", "Ctrl+7", "Summary, cases, dan evidence CSV", QStyle.StandardPixmap.SP_DialogSaveButton),
    NavigationRoute("about", "About", "SYSTEM", "Ctrl+8 / F1", "Versi dan reproduksibilitas", QStyle.StandardPixmap.SP_MessageBoxInformation),
)

ROUTES_BY_ID: Final = {route.route_id: route for route in NAVIGATION_ROUTES}


class NavigationItem(QFrame):
    clicked = Signal(str)

    def __init__(self, route: NavigationRoute, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.route = route
        self.button = QToolButton()
        self.button.setText(route.title)
        self.button.setIcon(self.style().standardIcon(route.icon))
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button.setCheckable(True)
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.button.setToolTip(f"{route.description} ({route.shortcut})")
        self.button.clicked.connect(
            lambda _checked=False: self.clicked.emit(route.route_id)
        )

        self.badge = QLabel("Belum siap")
        self.badge.setObjectName("navigationBadge")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.button, 1)
        layout.addWidget(self.badge)

    def set_active(self, active: bool) -> None:
        self.button.setChecked(active)

    def set_status(self, text: str, state: str = "idle") -> None:
        self.badge.setText(text)
        self.badge.setProperty("state", state)
        colors = {
            "idle": ("#d1d5db", "#374151"),
            "loading": ("#bfdbfe", "#1e40af"),
            "ready": ("#bbf7d0", "#166534"),
            "warning": ("#fde68a", "#92400e"),
            "error": ("#fecaca", "#991b1b"),
        }
        background, foreground = colors.get(state, colors["idle"])
        self.badge.setStyleSheet(
            f"background:{background}; color:{foreground}; border-radius:8px; "
            "padding:2px 7px; font-size:10px; font-weight:600;"
        )


class NavigationSidebar(QFrame):
    """Grouped, persistent route selector with per-route status badges."""

    route_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationSidebar")
        self.setFixedWidth(260)
        self._items: dict[str, NavigationItem] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(5)

        current_group = ""
        for route in NAVIGATION_ROUTES:
            if route.group != current_group:
                current_group = route.group
                heading = QLabel(current_group)
                heading.setObjectName("navigationGroup")
                layout.addSpacing(8)
                layout.addWidget(heading)
            item = NavigationItem(route)
            item.clicked.connect(self.route_requested)
            self._items[route.route_id] = item
            layout.addWidget(item)
        layout.addStretch(1)

        self.setStyleSheet(
            "#navigationSidebar { background:#172033; }"
            "#navigationGroup { color:#94a3b8; font-size:10px; font-weight:700; "
            "letter-spacing:1px; padding:5px 6px; }"
            "QToolButton { color:#e5e7eb; border:0; border-radius:5px; padding:9px; "
            "text-align:left; font-size:12px; }"
            "QToolButton:hover { background:#26334d; }"
            "QToolButton:checked { background:#2563eb; color:white; font-weight:700; }"
        )

    def route_ids(self) -> list[str]:
        return list(self._items)

    def set_current(self, route_id: str) -> None:
        for item_id, item in self._items.items():
            item.set_active(item_id == route_id)

    def set_status(self, route_id: str, text: str, state: str = "idle") -> None:
        self._items[route_id].set_status(text, state)

    def item(self, route_id: str) -> NavigationItem:
        return self._items[route_id]
