"""Reusable cards and controls for consistent, usable panel layouts."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.common.icons import app_icon


class IconButton(QToolButton):
    def __init__(self, icon_name: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setIcon(app_icon(icon_name))
        self.setToolTip(tooltip)
        self.setProperty("buttonRole", "ghost")
        self.setFixedSize(36, 36)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, icon_name: str | None = None) -> None:
        super().__init__(text)
        self.setProperty("buttonRole", "primary")
        if icon_name:
            self.setIcon(app_icon(icon_name, "#ffffff"))


class SecondaryButton(QPushButton):
    def __init__(self, text: str, icon_name: str | None = None) -> None:
        super().__init__(text)
        if icon_name:
            self.setIcon(app_icon(icon_name))


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__()
        self.title = QLabel(title)
        self.title.setProperty("role", "pageTitle")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setProperty("role", "pageSubtitle")
        self.subtitle.setWordWrap(True)
        self.actions = QHBoxLayout()
        self.actions.setContentsMargins(0, 0, 0, 0)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(self.title)
        text.addWidget(self.subtitle)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(text, 1)
        layout.addLayout(self.actions)


class SectionCard(QFrame):
    def __init__(self, title: str = "", subtitle: str = "") -> None:
        super().__init__()
        self.setProperty("card", True)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(16, 14, 16, 16)
        self.body.setSpacing(10)
        if title:
            label = QLabel(title)
            label.setProperty("role", "sectionTitle")
            self.body.addWidget(label)
        if subtitle:
            label = QLabel(subtitle)
            label.setProperty("role", "sectionSubtitle")
            label.setWordWrap(True)
            self.body.addWidget(label)


class MetricCard(QFrame):
    def __init__(self, label: str, value: str = "N/A", support: str = "") -> None:
        super().__init__()
        self.setProperty("card", True)
        self.label = QLabel(label)
        self.label.setProperty("role", "metricLabel")
        self.value = QLabel(value)
        self.value.setProperty("role", "metricValue")
        self.support = QLabel(support)
        self.support.setProperty("role", "sectionSubtitle")
        self.support.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 12)
        layout.setSpacing(2)
        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addWidget(self.support)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)


class StatusChip(QLabel):
    def __init__(self, text: str = "Idle", state: str = "idle") -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(text, state)

    def set_status(self, text: str, state: str) -> None:
        colors = {
            "idle": ("#e2e8f0", "#475569"),
            "loading": ("#dbeafe", "#1d4ed8"),
            "success": ("#dcfce7", "#166534"),
            "warning": ("#fef3c7", "#92400e"),
            "error": ("#fee2e2", "#991b1b"),
        }
        background, foreground = colors.get(state, colors["idle"])
        self.setText(text)
        self.setStyleSheet(
            f"background:{background};color:{foreground};border-radius:9px;"
            "padding:3px 9px;font-weight:700;"
        )


class EmptyState(QFrame):
    def __init__(self, title: str, message: str, icon_name: str = "info") -> None:
        super().__init__()
        self.setProperty("card", True)
        self.icon = QLabel()
        self.icon.setPixmap(app_icon(icon_name, "#64748b", 28).pixmap(28, 28))
        self.title = QLabel(title)
        self.title.setProperty("role", "sectionTitle")
        self.message = QLabel(message)
        self.message.setProperty("role", "sectionSubtitle")
        self.message.setWordWrap(True)
        self.action_layout = QHBoxLayout()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(self.action_layout)


class SearchField(QLineEdit):
    def __init__(self, placeholder: str) -> None:
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)


class TimelineStep(QFrame):
    def __init__(self, label: str) -> None:
        super().__init__()
        self.setProperty("card", True)
        self.label = QLabel(label)
        self.label.setProperty("role", "metricLabel")
        self.value = QLabel("Belum dipilih")
        self.value.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 10)
        layout.addWidget(self.label)
        layout.addWidget(self.value)
