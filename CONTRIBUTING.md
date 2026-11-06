# Contributing

Thank you for helping improve Steam Profile Insights.

## Development Setup

The project requires Python 3.13 or newer. From the repository root, create or
use the project virtual environment and install development dependencies:

### Windows PowerShell

```powershell
py -3.13 -m venv venv
.\venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### macOS/Linux

```bash
python3.13 -m venv venv
./venv/bin/python -m pip install -e ".[dev]"
```

Playwright Chromium is required for the review scraper:

```text
python -m playwright install chromium
```

## Quality Checks

Run the same checks locally that are required by CI:

```text
python -m ruff check main.py src tests
python -m pyright
python -m compileall -q main.py src tests
python -m pytest
```

Tests use sanitized fixtures and mocks. They do not require a Steam API key,
network access, or a browser during the test run.

## Pull Requests

- Keep changes focused and explain the user-visible or security impact.
- Add or update tests for behavior changes.
- Update README, CHANGELOG, or security documentation when relevant.
- Do not commit credentials, generated CSV files, logs, virtual environments,
  or build artifacts.
- Ensure CI passes before requesting review.

Pull requests are squash-merged into `main`. Release tags are created only
from reviewed commits on `main`.
