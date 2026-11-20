"""Core domain contracts and analytics services."""

from src.core.event_store import EventStore
from src.core.result import AnalysisResult

__all__ = ["AnalysisResult", "EventStore"]

