"""Full-height overlay navigation drawer and route definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.common.components import IconButton
from src.gui.common.icons import app_icon


@dataclass(frozen=True, slots=True)
class NavigationRoute:
    route_id: str
    title: str
    group: str
    shortcut: str
    description: str
    icon_name: str


NAVIGATION_ROUTES: Final[tuple[NavigationRoute, ...]] = (
    NavigationRoute("dataset", "Dataset & Status", "WORKSPACE", "Ctrl+1", "Import and validate an XES event log", "dataset"),
    NavigationRoute("overview", "Overview", "WORKSPACE", "Ctrl+2", "Inspect KPIs, activities, and cases", "overview"),
    NavigationRoute("exercise_11_7", "Outcome Kasus", "ANALYSES", "Ctrl+3", "Analisis cycle time dan outcome setiap kasus", "analytics"),
    NavigationRoute("rework", "Analisis Rework", "ANALYSES", "Ctrl+4", "Analisis aktivitas complete yang berulang", "rework"),
    NavigationRoute("sequence", "Urutan Cancel-Accept", "ANALYSES", "Ctrl+5", "Periksa urutan event cancel dan accept", "sequence"),
    NavigationRoute("explorer", "Penelusuran Kasus", "INVESTIGATION", "Ctrl+6", "Telusuri trace lengkap dan event pembukti", "explorer"),
    NavigationRoute("export", "Export", "OUTPUT", "Ctrl+7", "Write summary, cases, and evidence CSV", "export"),
    NavigationRoute("about", "About", "SYSTEM", "Ctrl+8 / F1", "View versions and reproducibility data", "info"),
)

ROUTES_BY_ID: Final = {route.route_id: route for route in NAVIGATION_ROUTES}


class DrawerScrim(QFrame):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background:rgba(15,23,42,115);")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
        event.accept()


class NavigationItem(QFrame):
    clicked = Signal(str)

    def __init__(self, route: NavigationRoute, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.route = route
        self.setObjectName("drawerNavigationItem")
        self.setProperty("active", False)

        self.button = QToolButton()
        self.button.setText(route.title)
        self.button.setIcon(app_icon(route.icon_name, "#cbd5e1"))
        self.button.setIconSize(QSize(20, 20))
        self.button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.button.setToolTip(f"{route.description} ({route.shortcut})")
        self.button.clicked.connect(
            lambda _checked=False: self.clicked.emit(route.route_id)
        )
        self.description = QLabel(route.description)
        self.description.setWordWrap(True)
        self.description.setObjectName("drawerNavigationDescription")
        self.badge = QLabel("Not ready")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        heading = QHBoxLayout()
        heading.setContentsMargins(0, 0, 0, 0)
        heading.addWidget(self.button, 1)
        heading.addWidget(self.badge)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 7)
        layout.setSpacing(0)
        layout.addLayout(heading)
        layout.addWidget(self.description)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)

    def set_status(self, text: str, state: str = "idle") -> None:
        self.badge.setText(text)
        colors = {
            "idle": ("#334155", "#cbd5e1"),
            "loading": ("#1e3a8a", "#bfdbfe"),
            "ready": ("#14532d", "#bbf7d0"),
            "warning": ("#78350f", "#fde68a"),
            "error": ("#7f1d1d", "#fecaca"),
        }
        background, foreground = colors.get(state, colors["idle"])
        self.badge.setStyleSheet(
            f"background:{background};color:{foreground};border-radius:8px;"
            "padding:2px 7px;font-size:10px;font-weight:700;"
        )


class NavigationSidebar(QFrame):
    """Overlay drawer with collapsible groups and descriptive route buttons."""

    route_requested = Signal(str)
    close_requested = Signal()

    DRAWER_WIDTH = 348

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navigationDrawer")
        self.setFixedWidth(self.DRAWER_WIDTH)
        self._items: dict[str, NavigationItem] = {}
        self._group_containers: dict[str, QWidget] = {}

        self.brand = QLabel("BPIC17 Workbench")
        self.brand.setObjectName("drawerBrand")
        self.close_button = IconButton("close", "Close navigation")
        self.close_button.setIcon(app_icon("close", "#e2e8f0"))
        self.close_button.clicked.connect(self.close_requested)
        brand_row = QHBoxLayout()
        brand_row.addWidget(self.brand, 1)
        brand_row.addWidget(self.close_button)

        self.dataset_name = QLabel("No active dataset")
        self.dataset_name.setObjectName("drawerDatasetName")
        self.dataset_meta = QLabel("Import an XES file to begin")
        self.dataset_meta.setObjectName("drawerDatasetMeta")
        dataset_card = QFrame()
        dataset_card.setObjectName("drawerDatasetCard")
        dataset_layout = QVBoxLayout(dataset_card)
        dataset_layout.setContentsMargins(11, 9, 11, 9)
        dataset_layout.addWidget(self.dataset_name)
        dataset_layout.addWidget(self.dataset_meta)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 18)
        content_layout.setSpacing(5)

        routes_by_group: dict[str, list[NavigationRoute]] = {}
        for route in NAVIGATION_ROUTES:
            routes_by_group.setdefault(route.group, []).append(route)

        for group, routes in routes_by_group.items():
            group_button = QToolButton()
            group_button.setText(group)
            group_button.setCheckable(True)
            group_button.setChecked(True)
            group_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            group_button.setIcon(app_icon("chevron_down", "#94a3b8", 14))
            group_button.setObjectName("drawerGroupButton")

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 6)
            container_layout.setSpacing(3)
            for route in routes:
                item = NavigationItem(route)
                item.clicked.connect(self.route_requested)
                self._items[route.route_id] = item
                container_layout.addWidget(item)
            self._group_containers[group] = container
            group_button.toggled.connect(
                lambda expanded, target=container, button=group_button: self._toggle_group(
                    target, button, expanded
                )
            )
            content_layout.addWidget(group_button)
            content_layout.addWidget(container)
        content_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(10)
        layout.addLayout(brand_row)
        layout.addWidget(dataset_card)
        layout.addWidget(scroll, 1)

        self.setStyleSheet(
            "#navigationDrawer { background:#111827; border-right:1px solid #334155; }"
            "#drawerBrand { color:white;font-size:17px;font-weight:800; }"
            "#drawerDatasetCard { background:#1e293b;border:1px solid #334155;border-radius:8px; }"
            "#drawerDatasetName { color:#f8fafc;font-weight:700; }"
            "#drawerDatasetMeta { color:#94a3b8;font-size:11px; }"
            "#drawerGroupButton { color:#94a3b8;border:0;background:transparent;"
            "font-size:10px;font-weight:800;letter-spacing:1px;text-align:left;padding:8px 5px; }"
            "#drawerNavigationItem { border:1px solid transparent;border-radius:7px;background:transparent; }"
            "#drawerNavigationItem:hover { background:#1e293b;border-color:#334155; }"
            "#drawerNavigationItem[active=true] { background:#1d4ed8;border-color:#3b82f6; }"
            "#drawerNavigationItem QToolButton { color:#f8fafc;border:0;background:transparent;"
            "font-weight:700;text-align:left;padding:3px; }"
            "#drawerNavigationDescription { color:#94a3b8;font-size:10px;padding-left:31px; }"
            "#drawerNavigationItem[active=true] #drawerNavigationDescription { color:#dbeafe; }"
            "QScrollArea { background:transparent; } QScrollArea > QWidget > QWidget { background:transparent; }"
            "QScrollBar:vertical { background:#111827;width:8px;margin:0; }"
            "QScrollBar::handle:vertical { background:#475569;border-radius:4px;min-height:32px; }"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }"
            "QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical { background:transparent; }"
        )

    def _toggle_group(
        self,
        container: QWidget,
        button: QToolButton,
        expanded: bool,
    ) -> None:
        container.setVisible(expanded)
        icon_name = "chevron_down" if expanded else "chevron_right"
        button.setIcon(app_icon(icon_name, "#94a3b8", 14))

    def route_ids(self) -> list[str]:
        return list(self._items)

    def set_current(self, route_id: str) -> None:
        for item_id, item in self._items.items():
            item.set_active(item_id == route_id)

    def set_status(self, route_id: str, text: str, state: str = "idle") -> None:
        self._items[route_id].set_status(text, state)

    def set_dataset_context(self, name: str, details: str) -> None:
        self.dataset_name.setText(name)
        self.dataset_meta.setText(details)

    def item(self, route_id: str) -> NavigationItem:
        return self._items[route_id]

    def group_container(self, group: str) -> QWidget:
        return self._group_containers[group]
