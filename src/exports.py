import csv

from config import config
from logging_utils import log
from models import AchievementResult, Game


def save_outputs(
    reviews: dict[int, str],
    games: list[Game],
    achievements_map: dict[int, AchievementResult],
) -> None:
    review_fields = ["AppID", "Game Title", "Review"]
    achievement_fields = [
        "AppID",
        "Game Title",
        "Playtime (h)",
        "Achievements Total",
        "Achievements Unlocked",
        "Completion %",
    ]
    with (
        open(config.REVIEWS_FILE, "w", newline="", encoding="utf-8") as reviews_file,
        open(
            config.ACHIEVEMENTS_FILE, "w", newline="", encoding="utf-8"
        ) as achievements_file,
    ):
        reviews_writer = csv.DictWriter(reviews_file, fieldnames=review_fields)
        achievements_writer = csv.DictWriter(
            achievements_file, fieldnames=achievement_fields
        )
        reviews_writer.writeheader()
        achievements_writer.writeheader()
        game_names = {game["appid"]: game["name"] for game in games}
        for app_id, text in reviews.items():
            reviews_writer.writerow(
                {
                    "AppID": app_id,
                    "Game Title": game_names.get(app_id, ""),
                    "Review": text,
                }
            )
        for game in games:
            appid = game["appid"]
            result = achievements_map.get(appid, AchievementResult(None, None))
            total, unlocked = result.total, result.unlocked
            completion = (
                round((unlocked / total) * 100, 2)
                if total is not None and unlocked is not None and total > 0
                else 0
                if total == 0 and unlocked == 0
                else None
            )
            achievements_writer.writerow(
                {
                    "AppID": appid,
                    "Game Title": game["name"],
                    "Playtime (h)": round(game["playtime_forever"] / 60, 2),
                    "Achievements Total": total,
                    "Achievements Unlocked": unlocked,
                    "Completion %": completion,
                }
            )
    log(
        f"Outputs saved: {config.REVIEWS_FILE}, {config.ACHIEVEMENTS_FILE}",
        source="save_outputs",
    )
