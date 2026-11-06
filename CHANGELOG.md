# Changelog

All notable changes to this project are documented in this file.

The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
uses [Semantic Versioning](https://semver.org/).

## [1.0.2] - 2026-11-06

### Added

- Added module, class, and function docstrings across the Python source and
  test modules.
- Documented the in-code API documentation in the README.

## [1.0.1] - 2026-11-06

### Changed

- Flattened the source layout so application modules are located directly
  under `src`.

## [1.0.0] - 2026-11-06

### Added

- Steam review scraping with Playwright.
- Steam Web API integration for owned games and achievements.
- Runtime validation for Steam API response structures.
- Concurrent achievement loading with bounded retries.
- CSV exports for reviews and achievement progress.
- Local virtual-environment bootstrapping.
- Typed application modules with strict Pyright checking.
- Unit tests and sanitized Steam API contract fixtures.
- GitHub Actions CI and tag-based release workflow.
- Dependabot configuration for Python and GitHub Actions dependencies.
- Threat model and MIT licensing.

[1.0.0]: https://github.com/ReaperN/steam-profile-insights/releases/tag/v1.0.0
[1.0.1]: https://github.com/ReaperN/steam-profile-insights/releases/tag/v1.0.1
