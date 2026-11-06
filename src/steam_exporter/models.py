from dataclasses import dataclass
from typing import TypedDict


class Game(TypedDict):
    appid: int
    name: str
    playtime_forever: int


@dataclass(slots=True)
class AchievementResult:
    total: int | None
    unlocked: int | None
