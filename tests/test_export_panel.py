"""GUI tests for A5 export, reset, rerun, and stale callback handling."""

from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog

from src.gui.panels.export_panel import ExportPanel
from tests.test_export import complete_results

_app = QApplication.instance() or QApplication([])


def test_export_panel_requires_dataset_results_and_directory(synthetic_store, tmp_path: Path) -> None:
    panel = ExportPanel()

    assert not panel.export_button.isEnabled()
    panel.set_store(synthetic_store)
    panel.set_results(complete_results())
    assert not panel.export_button.isEnabled()

    panel.set_output_directory(tmp_path)

    assert panel.export_button.isEnabled()
    assert panel.readiness.text() == "Hasil tersedia: 8/8"
    assert str(synthetic_store.metadata["dataset_name"]) in panel.dataset.text()


def test_export_panel_writes_files_and_reports_success(synthetic_store, tmp_path: Path) -> None:
    panel = ExportPanel()
    panel.set_store(synthetic_store)
    panel.set_results(complete_results())
    panel.set_output_directory(tmp_path)

    panel.export()

    assert panel.last_export is not None
    assert all(path.is_file() for path in panel.last_export.all())
    assert panel.status.property("statusState") == "ok"
    assert "Export selesai" in panel.status.text()


def test_export_panel_reports_export_failure(synthetic_store, tmp_path: Path) -> None:
    def fail_export(_results, _destination):
        raise PermissionError("read-only destination")

    panel = ExportPanel(exporter=fail_export)
    panel.set_store(synthetic_store)
    panel.set_results(complete_results())
    panel.set_output_directory(tmp_path)

    panel.export()

    assert panel.last_export is None
    assert panel.status.property("statusState") == "error"
    assert "read-only destination" in panel.status.text()


def test_cancel_directory_dialog_keeps_existing_destination(
    monkeypatch,
    synthetic_store,
    tmp_path: Path,
) -> None:
    panel = ExportPanel()
    panel.set_store(synthetic_store)
    panel.set_output_directory(tmp_path)
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *_args: "")

    panel.choose_directory()

    assert panel.output_path.text() == str(tmp_path)


def test_reset_and_rerun_controls_emit_requests(synthetic_store) -> None:
    panel = ExportPanel()
    reset_events: list[bool] = []
    rerun_events: list[bool] = []
    panel.reset_requested.connect(lambda: reset_events.append(True))
    panel.rerun_requested.connect(lambda: rerun_events.append(True))
    panel.set_store(synthetic_store)

    panel.reset_button.click()
    panel.rerun_button.click()

    assert reset_events == [True]
    assert rerun_events == [True]


def test_export_panel_ignores_stale_export_callback(
    synthetic_store,
    tmp_path: Path,
) -> None:
    pending = []

    def runner(job, on_done):
        pending.append((job, on_done))

    panel = ExportPanel(runner=runner)
    panel.set_store(synthetic_store)
    panel.set_results(complete_results())
    panel.set_output_directory(tmp_path)
    panel.export()
    job, on_done = pending[0]

    panel.set_store(None)
    on_done(job())

    assert panel.last_export is None
    assert panel.status.text() == "Belum ada dataset aktif."
