"""Tests for the repository-wide bytecode cache location."""

from importlib.util import cache_from_source
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_CACHE_ROOT = PROJECT_ROOT / ".pycache"


def test_python_uses_project_cache_prefix() -> None:
    assert sys.pycache_prefix is not None
    assert Path(sys.pycache_prefix).resolve() == PYTHON_CACHE_ROOT.resolve()


def test_source_bytecode_path_is_inside_central_cache() -> None:
    cache_path = Path(cache_from_source(str(PROJECT_ROOT / "src" / "main.py")))

    assert cache_path.resolve().is_relative_to(PYTHON_CACHE_ROOT.resolve())

