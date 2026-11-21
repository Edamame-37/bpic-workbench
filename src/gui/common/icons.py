"""Small monochrome vector icon set drawn with Qt primitives."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


@lru_cache(maxsize=128)
def app_icon(name: str, color: str = "#475569", size: int = 20) -> QIcon:
    """Return a crisp code-drawn icon without fonts, emoji, or external assets."""

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(color), max(1.5, size / 12))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    s = float(size)

    if name == "menu":
        for y in (0.28, 0.5, 0.72):
            painter.drawLine(QPointF(s * 0.2, s * y), QPointF(s * 0.8, s * y))
    elif name == "close":
        painter.drawLine(QPointF(s * 0.25, s * 0.25), QPointF(s * 0.75, s * 0.75))
        painter.drawLine(QPointF(s * 0.75, s * 0.25), QPointF(s * 0.25, s * 0.75))
    elif name in {"back", "forward", "chevron_left", "chevron_right"}:
        reverse = name in {"back", "chevron_left"}
        x1, x2 = (0.68, 0.32) if reverse else (0.32, 0.68)
        painter.drawLine(QPointF(s * x1, s * 0.24), QPointF(s * x2, s * 0.5))
        painter.drawLine(QPointF(s * x2, s * 0.5), QPointF(s * x1, s * 0.76))
        if name in {"back", "forward"}:
            tail = 0.78 if reverse else 0.22
            painter.drawLine(QPointF(s * x2, s * 0.5), QPointF(s * tail, s * 0.5))
    elif name in {"chevron_down", "chevron_up"}:
        up = name == "chevron_up"
        y1, y2 = (0.66, 0.36) if up else (0.36, 0.66)
        painter.drawLine(QPointF(s * 0.25, s * y1), QPointF(s * 0.5, s * y2))
        painter.drawLine(QPointF(s * 0.5, s * y2), QPointF(s * 0.75, s * y1))
    elif name == "dataset":
        for y in (0.25, 0.5, 0.75):
            painter.drawEllipse(QRectF(s * 0.2, s * (y - 0.12), s * 0.6, s * 0.23))
        painter.drawLine(QPointF(s * 0.2, s * 0.25), QPointF(s * 0.2, s * 0.75))
        painter.drawLine(QPointF(s * 0.8, s * 0.25), QPointF(s * 0.8, s * 0.75))
    elif name == "overview":
        for x, y in ((0.22, 0.22), (0.58, 0.22), (0.22, 0.58), (0.58, 0.58)):
            painter.drawRoundedRect(QRectF(s * x, s * y, s * 0.2, s * 0.2), 2, 2)
    elif name == "analytics":
        painter.drawLine(QPointF(s * 0.2, s * 0.8), QPointF(s * 0.2, s * 0.2))
        painter.drawLine(QPointF(s * 0.2, s * 0.8), QPointF(s * 0.82, s * 0.8))
        painter.drawLine(QPointF(s * 0.3, s * 0.65), QPointF(s * 0.48, s * 0.45))
        painter.drawLine(QPointF(s * 0.48, s * 0.45), QPointF(s * 0.64, s * 0.57))
        painter.drawLine(QPointF(s * 0.64, s * 0.57), QPointF(s * 0.82, s * 0.25))
    elif name == "rework":
        painter.drawArc(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6), 35 * 16, 285 * 16)
        painter.drawLine(QPointF(s * 0.22, s * 0.25), QPointF(s * 0.2, s * 0.48))
        painter.drawLine(QPointF(s * 0.22, s * 0.25), QPointF(s * 0.43, s * 0.28))
    elif name == "sequence":
        for x in (0.22, 0.5, 0.78):
            painter.setBrush(QColor(color))
            painter.drawEllipse(QPointF(s * x, s * 0.5), s * 0.07, s * 0.07)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(QPointF(s * 0.29, s * 0.5), QPointF(s * 0.43, s * 0.5))
        painter.drawLine(QPointF(s * 0.57, s * 0.5), QPointF(s * 0.71, s * 0.5))
    elif name in {"search", "explorer"}:
        painter.drawEllipse(QRectF(s * 0.2, s * 0.18, s * 0.45, s * 0.45))
        painter.drawLine(QPointF(s * 0.58, s * 0.58), QPointF(s * 0.82, s * 0.82))
    elif name == "export":
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.5, s * 0.6, s * 0.32), 2, 2)
        painter.drawLine(QPointF(s * 0.5, s * 0.15), QPointF(s * 0.5, s * 0.62))
        painter.drawLine(QPointF(s * 0.32, s * 0.34), QPointF(s * 0.5, s * 0.15))
        painter.drawLine(QPointF(s * 0.68, s * 0.34), QPointF(s * 0.5, s * 0.15))
    elif name == "info":
        painter.drawEllipse(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64))
        painter.drawPoint(QPointF(s * 0.5, s * 0.34))
        painter.drawLine(QPointF(s * 0.5, s * 0.47), QPointF(s * 0.5, s * 0.68))
    elif name == "folder":
        path = QPainterPath()
        path.moveTo(s * 0.16, s * 0.3)
        path.lineTo(s * 0.42, s * 0.3)
        path.lineTo(s * 0.5, s * 0.4)
        path.lineTo(s * 0.84, s * 0.4)
        path.lineTo(s * 0.78, s * 0.76)
        path.lineTo(s * 0.2, s * 0.76)
        path.closeSubpath()
        painter.drawPath(path)
    elif name in {"reset", "rerun"}:
        painter.drawArc(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6), 45 * 16, 275 * 16)
        painter.drawLine(QPointF(s * 0.18, s * 0.28), QPointF(s * 0.2, s * 0.5))
        painter.drawLine(QPointF(s * 0.18, s * 0.28), QPointF(s * 0.4, s * 0.3))
    elif name == "success":
        painter.drawEllipse(QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68))
        painter.drawLine(QPointF(s * 0.3, s * 0.5), QPointF(s * 0.45, s * 0.66))
        painter.drawLine(QPointF(s * 0.45, s * 0.66), QPointF(s * 0.72, s * 0.34))
    else:
        painter.drawRoundedRect(QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6), 3, 3)

    painter.end()
    return QIcon(pixmap)
