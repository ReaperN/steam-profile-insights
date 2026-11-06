# Threat Model

## Scope

This document describes the security properties and main threats of the Steam
Review & Achievement Scraper. It covers local execution, Steam API requests,
Playwright review scraping, generated files, and CI workflows.

## Assets

- `STEAM_API_KEY`
- `STEAM_ID`
- `STEAM_VANITY`
- Steam review and achievement data
- Generated CSV and log files
- The local Python environment and installed dependencies

## Trust Boundaries

1. **Local environment:** the operating-system keyring, environment variables,
   source code, virtual environment, generated files, and the user account.
2. **Steam services:** Steam Web API responses and Steam Community web pages
   are external inputs and are not trusted blindly.
3. **CI environment:** GitHub Actions executes repository code and handles
   build artifacts. Repository secrets must not be exposed to untrusted pull
   requests.

## Threats and Mitigations

| Threat | Mitigation |
| --- | --- |
| API keys or SteamIDs appear in logs | Centralized masking redacts configured secrets and `key=` query parameters. |
| Secrets are committed accidentally | Local users are directed to the OS keyring; environment variables remain an alternative for CI and unattended runs. Generated logs, CSV files, and virtual environments are ignored. |
| Unexpected Steam JSON breaks processing | Runtime validators reject malformed response structures and invalid field types. |
| Transient API failures cause incomplete results | Retry handling covers transient failures, honors `Retry-After`, and uses capped jittered backoff. |
| Excessive API requests | Achievement requests are limited to games with recorded playtime and use a bounded worker pool. |
| Browser resources remain open | Playwright browser contexts and browsers are closed in cleanup paths. |
| Dependency or workflow changes introduce risk | Dependabot monitors pip and GitHub Actions dependencies; CI runs linting, strict type checks, tests, and syntax checks. |
| Untrusted pull requests access release permissions | Release publishing is restricted to tag pushes and uses a separate workflow with explicit `contents: write` permission. |

## Residual Risks

- Steam API keys remain available to the local process and can be exposed by
  the host environment or other local software.
- The scraper processes external web content in a browser; Playwright and
  Chromium should be kept current.
- Runtime validation checks the response contract used by this application but
  does not prove that all Steam fields are semantically correct.
- The OS keyring protects the API key at rest for local use; the environment
  variable fallback remains exposed to the local process when configured.
- CSV output is not encrypted and should be protected by the host filesystem.

## Operational Guidance

- Never place secrets in source code, fixtures, issue reports, or pull requests.
- Prefer `python main.py --configure-api-key` for local use instead of storing
  the API key in an environment variable.
- Use `STEAM_API_KEY` only when keyring access is unavailable or the application
  runs unattended, such as in CI or on a server.
- Use a dedicated Steam API key with the minimum practical exposure.
- Review Dependabot pull requests and run the complete CI workflow before
  merging.
- Create releases only from reviewed commits using annotated version tags.
