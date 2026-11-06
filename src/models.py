"""Typed data structures shared by the Steam exporter modules."""

from dataclasses import dataclass
from typing import TypedDict


class Game(TypedDict):
    """Shape of a game record returned by the Steam Web API."""

    appid: int
    name: str
    playtime_forever: int


@dataclass(slots=True)
class AchievementResult:
    """Achievement totals for one game; None indicates an unavailable result."""

    total: int | None
    unlocked: int | None
