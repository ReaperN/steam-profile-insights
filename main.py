"""Compatibility entry point for running the Steam exporter from the project root."""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app import main  # noqa: E402
from bootstrap import bootstrap  # noqa: E402


def run() -> None:
    """Bootstrap the environment and start the application."""
    bootstrap()
    main()


if __name__ == "__main__":
    run()
