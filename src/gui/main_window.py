"""Application shell and initial navigation structure."""

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget, QVBoxLayout, QWidget

APPLICATION_TITLE = "BPIC17 Desktop Event Log Analyzer"

NAVIGATION_AREAS: tuple[tuple[str, str], ...] = (
    ("Dataset & Status", "Belum ada dataset aktif."),
    ("Overview", "Overview akan tersedia setelah loader XES diimplementasikan."),
    ("Exercise 11.7", "Analisis 11.7 A-E belum diimplementasikan."),
    ("Rework 11.15 & 11.18", "Analisis complete-only belum diimplementasikan."),
    ("Exercise 11.22", "Analisis eventually-follows belum diimplementasikan."),
    ("Case Explorer", "Case Explorer belum diimplementasikan."),
    ("Export", "Ekspor CSV belum diimplementasikan."),
    ("About", "BPIC Workbench versi 0.1.0 — fondasi awal."),
)


class MainWindow(QMainWindow):
    """Top-level shell that feature owners can populate independently."""

    def __init__(
        self,
        navigation_areas: Iterable[tuple[str, str]] = NAVIGATION_AREAS,
    ) -> None:
        super().__init__()
        self.setWindowTitle(APPLICATION_TITLE)
        self.resize(1100, 720)

        self.tabs = QTabWidget(self)
        for title, message in navigation_areas:
            self.tabs.addTab(self._build_placeholder_page(message), title)

        self.setCentralWidget(self.tabs)

    @staticmethod
    def _build_placeholder_page(message: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        return page

