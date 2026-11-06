# Steam Review & Achievement Scraper

A standalone Python utility that exports Steam reviews and achievement
progress to CSV files.

It is intended for Steam users, Steam Hunters users, and review writers who
want to inspect their own Steam reviews and achievement progress. Steam
Hunters users can use the exported achievement data alongside their profile
and game statistics, while review writers can use the review export to
review, search, and analyze their published reviews.

Example Steam Hunters profile:
[ReaperN on Steam Hunters](https://steamhunters.com/id/Reaper_N/games)

The application:

- fetches Steam reviews for a configured user with Playwright
- loads the user's games through the Steam Web API
- fetches achievements for played games concurrently
- retries transient achievement-request failures
- writes reviews and achievement data to separate CSV files

The project targets Python 3.13 and bootstraps a local virtual environment
automatically when run outside one.

## Features

- Playwright-based review scraping
- Steam Web API integration
- Parallel achievement requests with `ThreadPoolExecutor`
- One HTTP session per worker thread
- Retry handling for timeouts, HTTP 429, HTTP 5xx, and other transient errors
- Secret masking in log output
- Rotating application logs
- Defensive AppID parsing
- Progress display with `tqdm`
- Graceful `Ctrl+C` shutdown
- CSV output suitable for spreadsheets, pandas, and Power BI

## Requirements

- Python 3.13
- A Steam Web API key
- A Steam64 ID
- A Steam vanity name
- Internet access when running the scraper

The required runtime packages are:

- `playwright`
- `requests`
- `tenacity`
- `tqdm`

Development tools are declared in `pyproject.toml`:

- `pytest`
- `pyright`
- `ruff`

## Configuration

The application reads these environment variables:

| Variable | Description |
| --- | --- |
| `STEAM_API_KEY` | Steam Web API key |
| `STEAM_ID` | Steam64 ID of the account |
| `STEAM_VANITY` | Steam vanity name used for review URLs |

### Windows PowerShell

```powershell
setx STEAM_API_KEY "YOUR_API_KEY_HERE"
setx STEAM_ID "7656119XXXXXXXXXX"
setx STEAM_VANITY "YourVanityName"
```

Restart VS Code or open a new terminal after using `setx`.

To verify the variables in a new PowerShell session:

```powershell
echo $env:STEAM_API_KEY
echo $env:STEAM_ID
echo $env:STEAM_VANITY
```

The application validates all three values before starting the workflow.
Missing values raise a `ConfigurationError`.

## Installation and Usage

### Automatic setup

Run the script with Python 3.13:

```powershell
python main.py
```

When started outside a virtual environment, the script creates the local
`venv`, installs the runtime dependencies there, installs the Playwright
Chromium browser there, and restarts itself inside that environment. This
keeps the global Python installation free of project dependencies.

### Existing environment

Skip automatic bootstrapping when dependencies are already installed:

```powershell
python main.py --no-venv
```

The same behavior can be selected with:

```powershell
$env:NO_VENV_BOOTSTRAP = "1"
python main.py
```

This option assumes that the current Python environment already contains the
runtime dependencies.

After installing the package into the local project environment, the same
workflow can also be started with:

```powershell
.\venv\Scripts\python.exe -m pip install -e .
.\venv\Scripts\steam-exporter.exe
```

The console command does not create a virtual environment itself. Using the
explicit `venv` paths keeps the package, its dependencies, and the generated
console script out of the global Python installation.

### Run directly from the project environment

Windows:

```powershell
.\venv\Scripts\python.exe main.py
```

macOS/Linux:

```bash
./venv/bin/python main.py
```

The main workflow is:

1. scrape reviews
2. load the owned game list
3. request achievements for games with recorded playtime
4. write the CSV files

## Retry Behavior

Achievement requests allow up to three retries after the initial request.

- HTTP 400 and 403 are not retried because they indicate invalid or
  unauthorized requests.
- HTTP 429 honors the `Retry-After` header when available.
- Timeouts, HTTP 5xx responses, and other transient failures use exponential
  backoff with full jitter.
- Backoff delays are capped to prevent a single request from blocking
  indefinitely.

Games with zero recorded playtime are skipped for achievement requests.
Failed achievement requests are logged and represented by empty achievement
fields in the output.

## Output Files

The script writes these files in the project directory:

| File | Contents |
| --- | --- |
| `steam_reviews.csv` | `AppID`, game title, and review text |
| `steam_achievements.csv` | AppID, title, playtime, achievement totals, and completion percentage |
| `log.txt` | Application log |

Existing CSV files are overwritten on each successful run. The log uses a
rotating file handler with up to three backup files.

## Development

Install the project and development tools in the project virtual environment:

```powershell
.\venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run the local quality checks:

```powershell
.\venv\Scripts\ruff.exe format --check main.py src tests
.\venv\Scripts\ruff.exe check main.py src tests
.\venv\Scripts\pyright.exe
.\venv\Scripts\python.exe -m compileall -q main.py src tests
.\venv\Scripts\python.exe -m pytest
```

The test suite does not access Steam or require a browser. It includes:

- configuration and secret-masking tests
- retry behavior tests
- CSV export and zero-achievement edge-case tests
- mocked Steam game-list and achievement API tests
- a mocked Playwright review-extraction test
- contract tests using sanitized Steam response fixtures
- runtime validation for game and achievement response structures

## Continuous Integration

GitHub Actions is configured in
[`.github/workflows/ci.yml`](.github/workflows/ci.yml). On pushes and pull
requests it runs on Python 3.13 and performs:

1. syntax compilation
2. Ruff linting
3. strict Pyright type checking
4. pytest

## Releases and Dependency Updates

Releases are created from reviewed version tags matching `v*.*.*`, for
example:

```powershell
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

The release workflow builds a Python 3.13 wheel and attaches it to a GitHub
Release. It does not publish to PyPI.

Dependabot checks Python and GitHub Actions dependencies weekly. Dependency
updates still require review and passing CI before they are merged.

Security assumptions and residual risks are documented in
[THREAT_MODEL.md](THREAT_MODEL.md).

## License

This project is available under the [MIT License](LICENSE).

## Project Files

| Path | Purpose |
| --- | --- |
| `main.py` | Backward-compatible executable entry point |
| `src/steam_exporter/` | Application package split into focused modules |
| `src/steam_exporter/config.py` | Configuration and secret wrapper |
| `src/steam_exporter/models.py` | Typed game and achievement models |
| `src/steam_exporter/api.py` | Steam API clients, retries, and response validation |
| `src/steam_exporter/reviews.py` | Playwright review scraper |
| `src/steam_exporter/exports.py` | CSV output handling |
| `src/steam_exporter/app.py` | Workflow orchestration |
| `tests/test_main.py` | Unit and isolated integration-style tests |
| `tests/fixtures/` | Sanitized Steam API response fixtures |
| `pyproject.toml` | Packaging, dependencies, pytest, Ruff, and Pyright configuration |
| `.github/workflows/ci.yml` | Automated quality checks |
| `.github/workflows/release.yml` | Tag-based GitHub Release workflow |
| `.github/dependabot.yml` | Automated dependency update proposals |
| `THREAT_MODEL.md` | Assets, trust boundaries, mitigations, and residual risks |
| `.vscode/settings.json` | Selects the project virtual environment in VS Code |

## Logging and Secrets

API keys and SteamIDs are never written to logs in clear text. The logging
wrapper also redacts `key=` query parameter values.

Do not commit API keys, generated CSV files, logs, or the local virtual
environment. These generated or sensitive files are excluded by `.gitignore`.

## Deliberately Excluded Features

The following features are intentionally outside the current scope:

- achievement caching, because achievement definitions can change
- global achievement statistics for unplayed games
- JSON export
- additional Steam metadata such as genre, publisher, or release date
- packaging for distribution through PyPI
- network-dependent tests
