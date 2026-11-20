"""Project launcher with a repository-local Python bytecode cache."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
PYTHON_CACHE_ROOT = PROJECT_ROOT / ".pycache"
sys.pycache_prefix = str(PYTHON_CACHE_ROOT)


def run_application(arguments: list[str]) -> int:
    from src.main import main

    sys.argv = [sys.argv[0], *arguments]
    return main()


def run_tests(arguments: list[str]) -> int:
    import pytest

    return pytest.main(arguments)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python manage.py [run|test] [arguments]")
        return 2

    command, *arguments = sys.argv[1:]
    if command == "run":
        return run_application(arguments)
    if command == "test":
        return run_tests(arguments)

    print(f"Unknown command: {command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

