"""Header and global action bar for the application workspace."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class WorkspaceHeader(QFrame):
    back_requested = Signal()
    forward_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspaceHeader")
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.back_button.setFixedWidth(42)
        self.forward_button.setFixedWidth(42)
        self.back_button.setToolTip("Kembali (Alt+Left)")
        self.forward_button.setToolTip("Maju (Alt+Right)")
        self.back_button.clicked.connect(self.back_requested)
        self.forward_button.clicked.connect(self.forward_requested)

        self.title = QLabel("Dataset & Status")
        self.title.setObjectName("workspaceTitle")
        self.breadcrumb = QLabel("Workspace / Dataset & Status")
        self.breadcrumb.setObjectName("workspaceBreadcrumb")
        title_layout = QVBoxLayout()
        title_layout.setSpacing(1)
        title_layout.addWidget(self.title)
        title_layout.addWidget(self.breadcrumb)

        self.dataset = QLabel("Tidak ada dataset aktif")
        self.dataset.setObjectName("datasetContext")
        self.dataset.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.addWidget(self.back_button)
        layout.addWidget(self.forward_button)
        layout.addLayout(title_layout)
        layout.addStretch(1)
        layout.addWidget(self.dataset)

        self.setStyleSheet(
            "#workspaceHeader { background:white; border-bottom:1px solid #d1d5db; }"
            "#workspaceTitle { font-size:17px; font-weight:700; color:#111827; }"
            "#workspaceBreadcrumb { font-size:11px; color:#6b7280; }"
            "#datasetContext { color:#334155; font-size:11px; padding:6px 10px; "
            "background:#f1f5f9; border-radius:5px; }"
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
        self.import_button = QPushButton("Import XES")
        self.reset_button = QPushButton("Reset")
        self.rerun_button = QPushButton("Rerun All")
        self.export_button = QPushButton("Export")
        self.about_button = QPushButton("About")
        self.status = QLabel("Tidak ada dataset aktif")

        self.import_button.setToolTip("Pilih event log XES (Ctrl+O)")
        self.reset_button.setToolTip("Reset hasil tanpa membuang dataset")
        self.rerun_button.setToolTip("Jalankan ulang semua analisis (Ctrl+R)")
        self.export_button.setToolTip("Buka workspace Export")
        self.about_button.setToolTip("Informasi aplikasi (F1)")

        self.import_button.clicked.connect(self.import_requested)
        self.reset_button.clicked.connect(self.reset_requested)
        self.rerun_button.clicked.connect(self.rerun_requested)
        self.export_button.clicked.connect(self.export_requested)
        self.about_button.clicked.connect(self.about_requested)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 7, 10, 7)
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
            "#globalActionBar { background:#111827; border-top:1px solid #374151; }"
            "#globalActionBar QPushButton { color:#f9fafb; background:#273449; border:0; "
            "border-radius:4px; padding:7px 12px; }"
            "#globalActionBar QPushButton:hover { background:#3b82f6; }"
            "#globalActionBar QPushButton:disabled { color:#64748b; background:#1f2937; }"
            "#globalActionBar QLabel { color:#cbd5e1; }"
        )

    def set_dataset_active(self, active: bool) -> None:
        self.reset_button.setEnabled(active)
        self.rerun_button.setEnabled(active)
        self.export_button.setEnabled(active)
