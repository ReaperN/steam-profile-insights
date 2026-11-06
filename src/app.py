import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from api import (
    calculate_retry_delay,
    fetch_achievements,
    fetch_games,
    is_retryable_achievement_error,
    parse_achievements_response,
    parse_games_response,
)
from config import Config, ConfigurationError, Secret, config
from exports import save_outputs
from logging_utils import log
from models import AchievementResult, Game
from reviews import extract_reviews_playwright

__all__ = [
    "AchievementResult",
    "Config",
    "ConfigurationError",
    "Secret",
    "calculate_retry_delay",
    "config",
    "extract_reviews_playwright",
    "fetch_achievements",
    "fetch_games",
    "is_retryable_achievement_error",
    "parse_achievements_response",
    "parse_games_response",
    "save_outputs",
]


def fetch_all_achievements(
    games: list[Game],
) -> dict[int, AchievementResult]:
    results: dict[int, AchievementResult] = {}
    games_with_playtime = [game for game in games if game["playtime_forever"] > 0]
    log("Starting parallel achievement loading...", source="fetch_all_achievements")
    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_achievements, game["appid"]): game["appid"]
            for game in games_with_playtime
        }
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Loading achievements",
            unit="game",
            file=sys.stdout,
        ):
            appid = futures[future]
            if future.cancelled():
                log(
                    f"Future for AppID {appid} was cancelled.",
                    source="fetch_all_achievements",
                )
                results[appid] = AchievementResult(None, None)
                continue
            exception = future.exception()
            if exception is not None:
                log(
                    f"Future failed for AppID {appid}: {exception}",
                    source="fetch_all_achievements",
                )
                results[appid] = AchievementResult(None, None)
                continue
            appid_ret, total, unlocked = future.result()
            results[appid_ret] = AchievementResult(total, unlocked)
    log(
        f"Achievements loaded for {len(results)} games; "
        f"skipped {len(games) - len(games_with_playtime)} games without playtime",
        source="fetch_all_achievements",
    )
    return results


def main() -> None:
    try:
        config.validate()
        open(config.LOGFILE, "w").close()
        log("=== Start ===")
        print("Starting Playwright review scraper...")
        reviews = extract_reviews_playwright()
        print(f"Reviews found: {len(reviews)}")
        print("Loading Steam game list...")
        games = fetch_games()
        print("Loading achievements in parallel...")
        ach_start = time.time()
        achievements_map = fetch_all_achievements(games)
        print(f"Achievement loading time: {round(time.time() - ach_start, 2)} seconds")
        print("Saving CSV files...")
        save_outputs(reviews, games, achievements_map)
        print("DONE!")
        print(config.REVIEWS_FILE)
        print(config.ACHIEVEMENTS_FILE)
        print(f"Log: {config.LOGFILE}")
    except KeyboardInterrupt:
        log("Shutdown requested by user.", source="main", level="warning")
        print("\nShutdown requested. Resources were closed safely.")
