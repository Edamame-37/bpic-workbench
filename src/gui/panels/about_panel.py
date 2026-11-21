"""Runtime and active-dataset reproducibility information."""

from __future__ import annotations

import platform
import sys

import pandas as pd
import pm4py
import PySide6
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src import __version__
from src.core.event_store import EventStore


class AboutPanel(QWidget):
    """Show project, dependency, operating-system, and dataset metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title = QLabel(f"BPIC17 Desktop Event Log Analyzer {__version__}")
        self.title.setStyleSheet("font-size: 18px; font-weight: 700;")
        self.description = QLabel(
            "Aplikasi desktop PM4Py untuk delapan analisis BPIC17, evidence case, "
            "dan export CSV yang dapat direproduksi."
        )
        self.description.setWordWrap(True)
        self.runtime = QLabel(
            "\n".join(
                (
                    f"Python: {sys.version.split()[0]}",
                    f"PM4Py: {getattr(pm4py, '__version__', 'unknown')}",
                    f"pandas: {pd.__version__}",
                    f"PySide6: {PySide6.__version__}",
                    f"OS: {platform.platform()}",
                )
            )
        )
        self.runtime.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.dataset = QLabel("Dataset aktif: belum ada.")
        self.dataset.setWordWrap(True)
        self.dataset.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.description)
        layout.addWidget(QLabel("Environment:"))
        layout.addWidget(self.runtime)
        layout.addWidget(QLabel("Reproduksibilitas dataset:"))
        layout.addWidget(self.dataset)
        layout.addStretch(1)

    def set_store(self, store: EventStore | None) -> None:
        if store is None:
            self.dataset.setText("Dataset aktif: belum ada.")
            return
        metadata = store.metadata
        self.dataset.setText(
            "\n".join(
                (
                    f"File: {metadata.get('file_name', '-')}",
                    f"Ukuran: {metadata.get('file_size_bytes', '-')} byte",
                    f"SHA-256: {metadata.get('sha256', '-')}",
                    f"Case: {metadata.get('case_count', '-')}",
                    f"Event: {metadata.get('event_count', '-')}",
                )
            )
        )
