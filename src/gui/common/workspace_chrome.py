"""Website-style header and global toolbar for the workspace."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.gui.common.components import IconButton
from src.gui.common.icons import app_icon


class WorkspaceHeader(QFrame):
    menu_requested = Signal()
    back_requested = Signal()
    forward_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceHeader")
        self.menu_button = IconButton("menu", "Open navigation (Ctrl+B)")
        self.back_button = IconButton("back", "Back (Alt+Left)")
        self.forward_button = IconButton("forward", "Forward (Alt+Right)")
        self.menu_button.clicked.connect(self.menu_requested)
        self.back_button.clicked.connect(self.back_requested)
        self.forward_button.clicked.connect(self.forward_requested)

        self.title = QLabel("Dataset & Status")
        self.title.setProperty("role", "pageTitle")
        self.breadcrumb = QLabel("Workspace / Dataset & Status")
        self.breadcrumb.setProperty("role", "pageSubtitle")
        title_layout = QVBoxLayout()
        title_layout.setSpacing(0)
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.breadcrumb)

        self.dataset = QLabel("No active dataset")
        self.dataset.setObjectName("datasetContext")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 16, 8)
        layout.setSpacing(8)
        layout.addWidget(self.menu_button)
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addLayout(title_layout)
        layout.addStretch(1)
        layout.addWidget(self.dataset)

        self.setStyleSheet(
            "#workspaceHeader { background:white;border-bottom:1px solid #dfe6ef; }"
            "#datasetContext { color:#334155;font-size:11px;padding:8px 11px;"
            "background:#f1f5f9;border:1px solid #e2e8f0;border-radius:7px; }"
        )

    def set_route(self, title: str, context: str = "") -> None:
        self.title.setText(title)
        suffix = f" / {context}" if context else ""
        self.breadcrumb.setText(f"Workspace / {title}{suffix}")

    def set_dataset(self, text: str) -> None:
        self.dataset.setText(text)

    def set_history_available(self, *, back: bool, forward: bool) -> None:
        self.back_button.setEnabled(back)
        self.forward_button.setEnabled(forward)


class GlobalActionBar(QFrame):
    import_requested = Signal()
    reset_requested = Signal()
    rerun_requested = Signal()
    export_requested = Signal()
    about_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("globalActionBar")
        self.import_button = self._button("Import XES", "folder")
        self.reset_button = self._button("Reset", "reset")
        self.rerun_button = self._button("Rerun All", "rerun")
        self.export_button = self._button("Export", "export")
        self.about_button = self._button("About", "info")
        self.status = QLabel("No active dataset")

        self.import_button.setToolTip("Choose an event log (Ctrl+O)")
        self.reset_button.setToolTip("Clear results and keep the active dataset")
        self.rerun_button.setToolTip("Run all analyses again (Ctrl+R)")
        self.export_button.setToolTip("Open the export workspace")
        self.about_button.setToolTip("Open application information (F1)")
        self.import_button.clicked.connect(self.import_requested)
        self.reset_button.clicked.connect(self.reset_requested)
        self.rerun_button.clicked.connect(self.rerun_requested)
        self.export_button.clicked.connect(self.export_requested)
        self.about_button.clicked.connect(self.about_requested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(7)
        for button in (
            self.import_button,
            self.reset_button,
            self.rerun_button,
            self.export_button,
            self.about_button,
        ):
            layout.addWidget(button)
        layout.addStretch(1)
        layout.addWidget(self.status)

        self.setStyleSheet(
            "#globalActionBar { background:#111827;border-top:1px solid #334155; }"
            "#globalActionBar QPushButton { color:#f8fafc;background:#1e293b;border:1px solid #334155;"
            "border-radius:6px;padding:6px 11px; }"
            "#globalActionBar QPushButton:hover { background:#1d4ed8;border-color:#3b82f6; }"
            "#globalActionBar QPushButton:disabled { color:#64748b;background:#172033;border-color:#273449; }"
            "#globalActionBar QLabel { color:#cbd5e1; }"
        )

    @staticmethod
    def _button(text: str, icon_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setIcon(app_icon(icon_name, "#e2e8f0"))
        return button

    def set_dataset_active(self, active: bool) -> None:
        self.reset_button.setEnabled(active)
        self.rerun_button.setEnabled(active)
        self.export_button.setEnabled(active)
