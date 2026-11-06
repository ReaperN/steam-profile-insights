import datetime
import email.utils
import random
import threading
from collections.abc import Mapping
from typing import Any, cast

from requests import Session
from requests import exceptions as req_exceptions
from tenacity import retry, retry_if_exception, stop_after_attempt

from config import config
from logging_utils import log
from models import Game

MAX_RETRY_ATTEMPTS = 3
thread_local = threading.local()


def get_session() -> Session:
    if not hasattr(thread_local, "session"):
        thread_local.session = Session()
    return thread_local.session


def is_retryable_achievement_error(error: BaseException) -> bool:
    if isinstance(error, req_exceptions.HTTPError):
        status_code = error.response.status_code if error.response is not None else None
        return status_code not in {400, 403}
    return isinstance(error, (req_exceptions.RequestException, ValueError))


def calculate_retry_delay(
    delay: float, maximum: float, preserve_delay: bool = False
) -> float:
    delay = max(delay, 0)
    if preserve_delay:
        base_delay = min(delay, maximum)
        jitter_limit = min(base_delay, maximum - base_delay)
        return base_delay + random.uniform(0, jitter_limit)
    return random.uniform(0, min(delay, maximum))


def wait_for_achievement_retry(retry_state: Any) -> float:
    error = retry_state.outcome.exception()
    if isinstance(error, req_exceptions.HTTPError):
        response = error.response
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return calculate_retry_delay(
                        float(retry_after), 60, preserve_delay=True
                    )
                except ValueError:
                    try:
                        retry_at = email.utils.parsedate_to_datetime(retry_after)
                        if retry_at.tzinfo is None:
                            retry_at = retry_at.replace(tzinfo=datetime.timezone.utc)
                        delay = (
                            retry_at - datetime.datetime.now(datetime.timezone.utc)
                        ).total_seconds()
                        return calculate_retry_delay(delay, 60, preserve_delay=True)
                    except (TypeError, ValueError, OverflowError):
                        pass
    return calculate_retry_delay(2 ** max(retry_state.attempt_number - 1, 0), 30)


def parse_games_response(data: object) -> list[Game]:
    if not isinstance(data, Mapping):
        raise ValueError("Steam game response must be a JSON object")
    data = cast(Mapping[str, Any], data)
    response = data.get("response")
    if not isinstance(response, Mapping):
        raise ValueError("Steam game response is missing an object at 'response'")
    response = cast(Mapping[str, Any], response)
    raw_games = response.get("games")
    if not isinstance(raw_games, list):
        raise ValueError("Steam game response is missing a list at 'response.games'")
    raw_games = cast(list[Any], raw_games)
    games: list[Game] = []
    for index, raw_game in enumerate(raw_games):
        if not isinstance(raw_game, Mapping):
            raise ValueError(f"Steam game at index {index} must be a JSON object")
        raw_game = cast(Mapping[str, Any], raw_game)
        appid = raw_game.get("appid")
        name = raw_game.get("name")
        playtime = raw_game.get("playtime_forever")
        if (
            isinstance(appid, bool)
            or not isinstance(appid, int)
            or not isinstance(name, str)
            or isinstance(playtime, bool)
            or not isinstance(playtime, int)
        ):
            raise ValueError(
                f"Steam game at index {index} has invalid appid, name, or playtime"
            )
        games.append({"appid": appid, "name": name, "playtime_forever": playtime})
    return games


def parse_achievements_response(data: object) -> list[Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        raise ValueError("Steam achievement response must be a JSON object")
    data = cast(Mapping[str, Any], data)
    playerstats = data.get("playerstats")
    if not isinstance(playerstats, Mapping):
        raise ValueError(
            "Steam achievement response is missing an object at 'playerstats'"
        )
    playerstats = cast(Mapping[str, Any], playerstats)
    raw_achievements = playerstats.get("achievements")
    if not isinstance(raw_achievements, list):
        raise ValueError(
            "Steam achievement response is missing a list at 'playerstats.achievements'"
        )
    raw_achievements = cast(list[Any], raw_achievements)
    achievements: list[Mapping[str, Any]] = []
    for index, achievement in enumerate(raw_achievements):
        if not isinstance(achievement, Mapping):
            raise ValueError(
                f"Steam achievement at index {index} must be a JSON object"
            )
        achievement = cast(Mapping[str, Any], achievement)
        achieved = achievement.get("achieved")
        if isinstance(achieved, bool) or not isinstance(achieved, int):
            raise ValueError(
                f"Steam achievement at index {index} has an invalid 'achieved' value"
            )
        achievements.append(achievement)
    return achievements


@retry(
    wait=wait_for_achievement_retry,
    stop=stop_after_attempt(MAX_RETRY_ATTEMPTS + 1),
    retry=retry_if_exception(is_retryable_achievement_error),
    reraise=True,
)
def _fetch_achievements_with_retry(appid: int) -> tuple[int, int, int]:
    params = {"key": config.API_KEY.get(), "steamid": config.STEAM_ID, "appid": appid}
    response = get_session().get(
        "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    achievements = parse_achievements_response(response.json())
    return (
        appid,
        len(achievements),
        sum(1 for achievement in achievements if achievement.get("achieved") == 1),
    )


def fetch_achievements(appid: int) -> tuple[int, int | None, int | None]:
    try:
        return _fetch_achievements_with_retry(appid)
    except (req_exceptions.RequestException, ValueError) as error:
        log(
            f"Failed to load achievements for {appid}: {error}",
            source="fetch_achievements",
        )
        return appid, None, None


def fetch_games() -> list[Game]:
    params = {
        "key": config.API_KEY.get(),
        "steamid": config.STEAM_ID,
        "include_appinfo": True,
        "include_played_free_games": True,
    }
    response = get_session().get(
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    games = parse_games_response(response.json())
    log(f"Game list loaded: {len(games)} games", source="fetch_games")
    return games
