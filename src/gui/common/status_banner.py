"""Reusable status label with consistent application states."""

from typing import Final

from PySide6.QtWidgets import QLabel, QWidget

_STYLES: Final[dict[str, str]] = {
    "idle": "color: #444444; padding: 6px;",
    "loading": "color: #075985; background: #e0f2fe; padding: 6px;",
    "ok": "color: #166534; background: #dcfce7; padding: 6px;",
    "warning": "color: #854d0e; background: #fef9c3; padding: 6px;",
    "error": "color: #991b1b; background: #fee2e2; padding: 6px;",
}


class StatusBanner(QLabel):
    """Display idle, progress, success, warning, and error messages."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.set_state("idle", text)

    def set_state(self, state: str, text: str) -> None:
        if state not in _STYLES:
            raise ValueError(f"Unsupported status state: {state}")
        self.setProperty("statusState", state)
        self.setStyleSheet(_STYLES[state])
        self.setText(text)

    def set_idle(self, text: str) -> None:
        self.set_state("idle", text)

    def set_loading(self, text: str) -> None:
        self.set_state("loading", text)

    def set_success(self, text: str) -> None:
        self.set_state("ok", text)

    def set_warning(self, text: str) -> None:
        self.set_state("warning", text)

    def set_error(self, text: str) -> None:
        self.set_state("error", text)
