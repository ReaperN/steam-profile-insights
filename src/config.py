"""Configuration values, environment lookup, and secret handling."""

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Secret:
    """Wrap a sensitive value so it is not exposed by normal representations."""

    _value: str | None = field(repr=False)

    def get(self) -> str | None:
        """Return the wrapped secret for an authenticated request."""
        return self._value

    def __repr__(self) -> str:
        """Return a redacted representation."""
        return "<SecretValue>"


class ConfigurationError(Exception):
    """Raised when required Steam configuration is missing."""


def _get_env(name: str) -> str | None:
    """Read a setting from the environment, including Windows user variables."""
    value = os.getenv(name)
    if value:
        return value

    if os.name != "nt":
        return None

    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            try:
                value, _ = winreg.QueryValueEx(key, name)
            except FileNotFoundError:
                return None
            return value or None
    except OSError:
        return None


@dataclass(slots=True)
class Config:
    """Runtime settings for Steam access, scraping, output, and logging."""
    API_KEY: Secret = field(default_factory=lambda: Secret(_get_env("STEAM_API_KEY")))
    STEAM_ID: str | None = field(default_factory=lambda: _get_env("STEAM_ID"))
    STEAM_VANITY: str | None = field(default_factory=lambda: _get_env("STEAM_VANITY"))
    MAX_PAGES: int = 20
    MAX_WORKERS: int = 16
    REVIEWS_FILE: str = "steam_reviews.csv"
    ACHIEVEMENTS_FILE: str = "steam_achievements.csv"
    LOGFILE: str = "log.txt"

    def validate(self) -> None:
        """Raise ConfigurationError when a required setting is missing."""
        if not self.API_KEY.get():
            raise ConfigurationError("STEAM_API_KEY is missing!")
        if not self.STEAM_ID:
            raise ConfigurationError("STEAM_ID is missing!")
        if not self.STEAM_VANITY:
            raise ConfigurationError("STEAM_VANITY is missing!")


config = Config()
