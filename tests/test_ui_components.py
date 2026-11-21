"""Contract tests for shared website-style GUI components."""

from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QLabel,
    QTabBar,
    QTableWidget,
)

from src.gui.common import EmptyState, MetricCard, PageHeader, SectionCard, app_icon
from src.gui.main_window import MainWindow

_app = QApplication.instance() or QApplication([])


def test_vector_icons_are_available_without_font_glyphs() -> None:
    for name in (
        "menu",
        "close",
        "dataset",
        "overview",
        "analytics",
        "rework",
        "sequence",
        "explorer",
        "export",
        "info",
    ):
        assert not app_icon(name).isNull()


def test_shared_cards_expose_content_and_semantic_text() -> None:
    header = PageHeader("Title", "Description")
    card = SectionCard("Section", "Supporting text")
    metric = MetricCard("Cases", "42", "active dataset")
    empty = EmptyState("No results", "Run the analysis first")

    assert header.title.text() == "Title"
    assert card.property("card") is True
    assert metric.value.text() == "42"
    assert empty.message.text() == "Run the analysis first"


def test_application_uses_functional_analysis_terminology() -> None:
    window = MainWindow()
    try:
        texts = [label.text() for label in window.findChildren(QLabel)]
        texts.extend(button.text() for button in window.findChildren(QAbstractButton))
        for tab_bar in window.findChildren(QTabBar):
            texts.extend(tab_bar.tabText(index) for index in range(tab_bar.count()))
        for table in window.findChildren(QTableWidget):
            texts.extend(
                item.text()
                for column in range(table.columnCount())
                if (item := table.horizontalHeaderItem(column)) is not None
            )

        rendered_text = " ".join(texts).casefold()
        assert "exercise" not in rendered_text
        assert "latihan" not in rendered_text
        assert "repeated complete" in rendered_text
        assert "same resource complete" in rendered_text
        assert "outcome kasus" in rendered_text
        assert "urutan cancel-accept" in rendered_text
    finally:
        window.close()
