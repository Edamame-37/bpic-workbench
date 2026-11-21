"""Contract tests for shared website-style GUI components."""

from PySide6.QtWidgets import QApplication

from src.gui.common import EmptyState, MetricCard, PageHeader, SectionCard, app_icon

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
