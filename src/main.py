"""Executable entry point for the BPIC Workbench desktop application."""

import sys
from collections.abc import Sequence

from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def create_application(arguments: Sequence[str] | None = None) -> QApplication:
    """Return the current QApplication or create one for this process."""

    existing_application = QApplication.instance()
    if existing_application is not None:
        if not isinstance(existing_application, QApplication):
            raise RuntimeError("An incompatible Qt application already exists")
        return existing_application

    return QApplication(list(arguments) if arguments is not None else sys.argv)


def main() -> int:
    application = create_application()
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

