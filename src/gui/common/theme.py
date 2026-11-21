"""Application-wide website-style visual tokens and Qt stylesheet."""

APP_STYLESHEET = """
QWidget { color:#172033; font-size:12px; }
QMainWindow, QWidget#workspaceRoot { background:#f4f7fb; }
QFrame[card="true"] { background:white; border:1px solid #dfe6ef; border-radius:8px; }
QLabel[role="pageTitle"] { font-size:22px; font-weight:700; color:#0f172a; }
QLabel[role="pageSubtitle"] { color:#64748b; }
QLabel[role="sectionTitle"] { font-size:14px; font-weight:700; color:#172033; }
QLabel[role="sectionSubtitle"] { color:#64748b; }
QLabel[role="metricValue"] { font-size:22px; font-weight:700; color:#0f172a; }
QLabel[role="metricLabel"] { color:#64748b; font-weight:600; }
QPushButton, QToolButton { min-height:30px; border:1px solid #cbd5e1; border-radius:6px; padding:4px 12px; background:white; }
QPushButton:hover, QToolButton:hover { border-color:#2563eb; background:#eff6ff; }
QPushButton:focus, QToolButton:focus, QLineEdit:focus, QComboBox:focus { border:2px solid #2563eb; }
QPushButton:disabled, QToolButton:disabled { color:#94a3b8; background:#f1f5f9; border-color:#e2e8f0; }
QPushButton[buttonRole="primary"] { color:white; background:#2563eb; border-color:#2563eb; font-weight:700; }
QPushButton[buttonRole="primary"]:hover { background:#1d4ed8; }
QPushButton[buttonRole="ghost"], QToolButton[buttonRole="ghost"] { border-color:transparent; background:transparent; }
QLineEdit, QComboBox { min-height:32px; border:1px solid #cbd5e1; border-radius:6px; padding:2px 9px; background:white; }
QTableView, QTableWidget { background:white; alternate-background-color:#f8fafc; border:1px solid #dfe6ef; border-radius:6px; gridline-color:#e2e8f0; selection-background-color:#dbeafe; selection-color:#172033; }
QHeaderView::section { background:#f8fafc; color:#475569; font-weight:700; border:0; border-bottom:1px solid #dfe6ef; padding:7px; }
QTabWidget::pane { border:1px solid #dfe6ef; border-radius:7px; background:white; }
QTabBar::tab { padding:8px 16px; color:#64748b; background:#f1f5f9; }
QTabBar::tab:selected { color:#1d4ed8; background:white; font-weight:700; }
QSplitter::handle { background:#e2e8f0; }
"""
