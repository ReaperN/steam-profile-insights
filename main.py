import sys
from pathlib import Path

SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from steam_exporter.app import main  # noqa: E402
from steam_exporter.bootstrap import bootstrap  # noqa: E402


def run() -> None:
    bootstrap()
    main()


if __name__ == "__main__":
    run()
