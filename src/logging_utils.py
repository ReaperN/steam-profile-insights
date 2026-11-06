"""Logging setup with redaction of Steam credentials and user identifiers."""

import logging
import logging.handlers
import re
from typing import Literal

from config import config


def mask_secrets(text: object) -> str | None:
    """Replace configured secrets and URL keys with safe placeholders."""
    if text is None:
        return text
    value = str(text)
    api = config.API_KEY.get()
    if api:
        value = value.replace(api, "<REDACTED_API_KEY>")
    if config.STEAM_ID:
        value = value.replace(config.STEAM_ID, "<REDACTED_STEAMID>")
    return re.sub(
        r"([?&]key=)[^&\s]+",
        r"\1<REDACTED>",
        value,
        flags=re.IGNORECASE,
    )


logger = logging.getLogger("steam_scraper")
logger.setLevel(logging.INFO)
try:
    handler = logging.handlers.RotatingFileHandler(
        config.LOGFILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
except OSError:
    handler = logging.FileHandler(config.LOGFILE, encoding="utf-8")
handler.setFormatter(
    logging.Formatter("%(asctime)s %(message)s", datefmt="[%Y-%m-%d %H:%M:%S]")
)
logger.addHandler(handler)

LogLevel = Literal["debug", "info", "warning", "error", "critical", "exception"]


def log(msg: object, source: str | None = None, level: LogLevel = "info") -> None:
    """Write a masked message at the requested log level."""
    masked_msg = mask_secrets(msg)
    final = f"SOURCE: {mask_secrets(source)} {masked_msg}" if source else masked_msg
    if level == "exception":
        logger.exception(final)
    else:
        getattr(logger, level)(final)
