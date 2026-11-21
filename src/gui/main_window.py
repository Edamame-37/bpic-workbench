"""Disco-inspired application workspace for BPIC17 analysis panels."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.event_store import EventStore
from src.core.result import AnalysisResult
from src.gui.common import (
    NAVIGATION_ROUTES,
    ROUTES_BY_ID,
    GlobalActionBar,
    NavigationSidebar,
    WorkspaceHeader,
)
from src.gui.panels.about_panel import AboutPanel
from src.gui.panels.case_explorer_panel import CaseExplorerPanel
from src.gui.panels.dataset_panel import DatasetPanel
from src.gui.panels.exercise_11_7_panel import Exercise117Panel
from src.gui.panels.export_panel import ExportPanel
from src.gui.panels.overview_panel import OverviewPanel
from src.gui.panels.rework_panel import ReworkPanel
from src.gui.panels.sequence_panel import SequencePanel
from src.gui.worker import WorkerManager

APPLICATION_TITLE = "BPIC17 Desktop Event Log Analyzer"
NAVIGATION_AREAS = tuple(
    (route.title, route.description) for route in NAVIGATION_ROUTES
)


class MainWindow(QMainWindow):
    """Coordinate dataset state, navigation, analyses, and global actions."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APPLICATION_TITLE)
        self.resize(1280, 820)

        self.worker_manager = WorkerManager(self)
        runner = self.worker_manager.run

        self.dataset_panel = DatasetPanel(runner=runner)
        self.overview_panel = OverviewPanel(runner=runner)
        self.exercise_11_7_panel = Exercise117Panel(runner=runner)
        self.rework_panel = ReworkPanel(runner=runner)
        self.sequence_panel = SequencePanel(runner=runner)
        self.case_explorer_panel = CaseExplorerPanel()
        self.export_panel = ExportPanel(runner=runner)
        self.about_panel = AboutPanel()

        self._panels: dict[str, QWidget] = {
            "dataset": self.dataset_panel,
            "overview": self.overview_panel,
            "exercise_11_7": self.exercise_11_7_panel,
            "rework": self.rework_panel,
            "sequence": self.sequence_panel,
            "explorer": self.case_explorer_panel,
            "export": self.export_panel,
            "about": self.about_panel,
        }

        self.sidebar = NavigationSidebar()
        self.header = WorkspaceHeader()
        self.action_bar = GlobalActionBar()
        self.pages = QStackedWidget()
        self._page_indexes: dict[str, int] = {}
        for route in NAVIGATION_ROUTES:
            self._page_indexes[route.route_id] = self.pages.addWidget(
                self._panels[route.route_id]
            )

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.sidebar)
        body.addWidget(self.pages, 1)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.header)
        central_layout.addLayout(body, 1)
        central_layout.addWidget(self.action_bar)
        self.setCentralWidget(central)

        self._history = ["dataset"]
        self._history_index = 0
        self._shortcut_actions: dict[str, QAction] = {}

        self._connect_signals()
        self._install_shortcuts()
        self.action_bar.set_dataset_active(False)
        self.navigate("dataset", record_history=False)
        self._refresh_navigation_state()

    def _connect_signals(self) -> None:
        self.sidebar.route_requested.connect(self.navigate)
        self.header.back_requested.connect(self.go_back)
        self.header.forward_requested.connect(self.go_forward)

        self.action_bar.import_requested.connect(self._import_dataset)
        self.action_bar.reset_requested.connect(self._reset_results)
        self.action_bar.rerun_requested.connect(self._rerun_results)
        self.action_bar.export_requested.connect(lambda: self.navigate("export"))
        self.action_bar.about_requested.connect(lambda: self.navigate("about"))

        self.dataset_panel.store_changed.connect(self._set_store)
        self.dataset_panel.load_started.connect(self._on_load_started)
        self.dataset_panel.load_failed.connect(self._on_load_failed)
        self.overview_panel.open_case_requested.connect(self._open_case)
        self.exercise_11_7_panel.open_case_requested.connect(self._open_case)
        self.rework_panel.open_case_requested.connect(self._open_case)
        self.sequence_panel.open_case_requested.connect(self._open_case)
        self.exercise_11_7_panel.results_changed.connect(self._sync_export_results)
        self.rework_panel.results_changed.connect(self._sync_export_results)
        self.sequence_panel.results_changed.connect(self._sync_export_results)
        self.case_explorer_panel.case_changed.connect(self._on_case_changed)
        self.export_panel.reset_requested.connect(self._reset_results)
        self.export_panel.rerun_requested.connect(self._rerun_results)
        self.export_panel.state_changed.connect(self._on_export_state_changed)

    def _install_shortcuts(self) -> None:
        route_shortcuts = {
            "dataset": "Ctrl+1",
            "overview": "Ctrl+2",
            "exercise_11_7": "Ctrl+3",
            "rework": "Ctrl+4",
            "sequence": "Ctrl+5",
            "explorer": "Ctrl+6",
            "export": "Ctrl+7",
            "about": "Ctrl+8",
        }
        for route_id, shortcut in route_shortcuts.items():
            self._add_shortcut(
                f"route:{route_id}", shortcut, lambda route=route_id: self.navigate(route)
            )
        self._add_shortcut("import", "Ctrl+O", self._import_dataset)
        self._add_shortcut("rerun", "Ctrl+R", self._rerun_results)
        self._add_shortcut("back", "Alt+Left", self.go_back)
        self._add_shortcut("forward", "Alt+Right", self.go_forward)
        self._add_shortcut("about", "F1", lambda: self.navigate("about"))

    def _add_shortcut(
        self,
        name: str,
        shortcut: str,
        callback: Callable[[], None],
    ) -> None:
        action = QAction(self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(lambda _checked=False: callback())
        self.addAction(action)
        self._shortcut_actions[name] = action

    def navigate(self, route_id: str, record_history: bool = True) -> None:
        """Show one workspace route and optionally add it to navigation history."""

        if route_id not in self._page_indexes:
            raise ValueError(f"Unknown navigation route: {route_id}")
        if record_history and self.current_route() != route_id:
            self._history = self._history[: self._history_index + 1]
            self._history.append(route_id)
            self._history_index = len(self._history) - 1

        self.pages.setCurrentIndex(self._page_indexes[route_id])
        self.sidebar.set_current(route_id)
        route = ROUTES_BY_ID[route_id]
        context = ""
        if route_id == "explorer" and self.case_explorer_panel.current_case:
            context = f"Case {self.case_explorer_panel.current_case}"
        self.header.set_route(route.title, context)
        self._update_history_actions()

    def current_route(self) -> str:
        current = self.pages.currentWidget()
        for route_id, panel in self._panels.items():
            if panel is current:
                return route_id
        return "dataset"

    def go_back(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self.navigate(self._history[self._history_index], record_history=False)

    def go_forward(self) -> None:
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self.navigate(self._history[self._history_index], record_history=False)

    def _update_history_actions(self) -> None:
        self.header.set_history_available(
            back=self._history_index > 0,
            forward=self._history_index < len(self._history) - 1,
        )

    def _import_dataset(self) -> None:
        self.navigate("dataset")
        self.dataset_panel.choose_file()

    def _on_load_started(self, path: str) -> None:
        self.sidebar.set_status("dataset", "Loading", "loading")
        self.header.set_dataset(f"Memuat: {path}")
        self.action_bar.status.setText("Import XES berjalan...")

    def _on_load_failed(self, message: str) -> None:
        self.sidebar.set_status("dataset", "Error", "error")
        self.header.set_dataset("Import gagal")
        self.action_bar.status.setText(message)
        self.navigate("dataset")

    def _set_store(self, store: EventStore | None) -> None:
        self.export_panel.set_store(store)
        self.about_panel.set_store(store)
        self.overview_panel.set_store(store)
        self.exercise_11_7_panel.set_store(store)
        self.rework_panel.set_store(store)
        self.sequence_panel.set_store(store)
        self.case_explorer_panel.set_store(store)
        self._sync_export_results()

        if store is None:
            self.header.set_dataset("Tidak ada dataset aktif")
            self.action_bar.status.setText("Tidak ada dataset aktif")
            self.action_bar.set_dataset_active(False)
            self.navigate("dataset")
        else:
            metadata = store.metadata
            name = metadata.get("file_name", metadata.get("dataset_name", "-"))
            cases = metadata.get("case_count", "-")
            events = metadata.get("event_count", "-")
            self.header.set_dataset(f"{name}  ·  {cases} case  ·  {events} event")
            self.action_bar.status.setText(f"Dataset aktif: {name}")
            self.action_bar.set_dataset_active(True)
            self.navigate("overview")
        self._refresh_navigation_state()

    def _open_case(self, case_id: str, row_ids: list[object]) -> None:
        self.case_explorer_panel.open_case(case_id, row_ids)
        self.navigate("explorer")

    def _on_case_changed(self, case_id: object) -> None:
        self._refresh_navigation_state()
        if self.current_route() == "explorer":
            context = f"Case {case_id}" if case_id else ""
            self.header.set_route(ROUTES_BY_ID["explorer"].title, context)

    def _collect_results(self) -> list[AnalysisResult]:
        return [
            *self.exercise_11_7_panel.results(),
            *self.rework_panel.results(),
            *self.sequence_panel.results(),
        ]

    def _sync_export_results(self) -> None:
        self.export_panel.set_results(self._collect_results())
        self._refresh_navigation_state()

    def _reset_results(self) -> None:
        """Clear derived results while preserving the parsed EventStore."""

        self.overview_panel.reset()
        self.exercise_11_7_panel.reset()
        self.rework_panel.reset_results()
        self.sequence_panel.reset()
        self.case_explorer_panel.clear_selection()
        self._sync_export_results()

    def _rerun_results(self) -> None:
        """Recompute all analyses from the active store without parsing XES again."""

        if self.dataset_panel.store() is None:
            return
        self._reset_results()
        self.overview_panel.refresh()
        self.exercise_11_7_panel.run()
        self.rework_panel.run_analysis()
        self.sequence_panel.run()

    def _on_export_state_changed(self, state: str) -> None:
        if state == "exporting":
            self.sidebar.set_status("export", "Exporting", "loading")
        elif state == "success":
            self.sidebar.set_status("export", "Saved", "ready")
        elif state == "error":
            self.sidebar.set_status("export", "Error", "error")
        else:
            self._refresh_navigation_state()

    def _refresh_navigation_state(self) -> None:
        store = self.dataset_panel.store()
        self.sidebar.set_status("about", "Info", "ready")
        if store is None:
            self.sidebar.set_status("dataset", "No data", "warning")
            for route_id in (
                "overview",
                "exercise_11_7",
                "rework",
                "sequence",
                "explorer",
                "export",
            ):
                self.sidebar.set_status(route_id, "No data", "idle")
            return

        self.sidebar.set_status("dataset", "Ready", "ready")
        self.sidebar.set_status("overview", "Ready", "ready")
        self._set_result_status(
            "exercise_11_7", self.exercise_11_7_panel.results(), 5
        )
        self._set_result_status("rework", self.rework_panel.results(), 2)
        self._set_result_status("sequence", self.sequence_panel.results(), 1)
        case_id = self.case_explorer_panel.current_case
        self.sidebar.set_status(
            "explorer",
            f"Case {case_id}" if case_id else "Ready",
            "ready" if case_id else "idle",
        )
        results = self._collect_results()
        export_ready = len(results) == 8
        self.sidebar.set_status(
            "export",
            f"{len(results)}/8",
            "ready" if export_ready else "warning",
        )

    def _set_result_status(
        self,
        route_id: str,
        results: list[AnalysisResult],
        expected: int,
    ) -> None:
        if not results:
            self.sidebar.set_status(route_id, f"0/{expected}", "warning")
            return
        state = "ready" if all(result.status == "ok" for result in results) else "warning"
        self.sidebar.set_status(route_id, f"{len(results)}/{expected}", state)
