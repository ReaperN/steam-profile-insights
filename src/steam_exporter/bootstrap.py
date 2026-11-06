import os
import subprocess
import sys

VENV_DIR = "venv"
PYTHON_BIN = (
    os.path.join(VENV_DIR, "Scripts", "python.exe")
    if os.name == "nt"
    else os.path.join(VENV_DIR, "bin", "python")
)
REQUIRED_PACKAGES = ["requests", "tenacity", "tqdm", "playwright"]


def create_venv() -> None:
    print("Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])


def install_packages() -> None:
    print("Installing required packages...")
    subprocess.check_call([PYTHON_BIN, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([PYTHON_BIN, "-m", "pip", "install"] + REQUIRED_PACKAGES)
    subprocess.check_call([PYTHON_BIN, "-m", "playwright", "install", "chromium"])


def restart_in_venv() -> None:
    print("Restarting script inside virtual environment...")
    os.execv(PYTHON_BIN, [PYTHON_BIN] + sys.argv)


def in_venv() -> bool:
    return sys.prefix != sys.base_prefix


def bootstrap() -> None:
    skip_bootstrap = "--no-venv" in sys.argv or os.getenv("NO_VENV_BOOTSTRAP") == "1"
    if not in_venv() and not skip_bootstrap:
        if not os.path.exists(VENV_DIR):
            create_venv()
            install_packages()
        restart_in_venv()
    print("Virtual environment active - script is running in isolation.")
