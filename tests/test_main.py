import csv
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from requests import Response
from requests import exceptions as req_exceptions

import steam_exporter as main
import steam_exporter.api as api
import steam_exporter.logging_utils as logging_utils
import steam_exporter.reviews as reviews_module

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> object:
    with open(FIXTURES_DIR / name, encoding="utf-8") as file:
        return json.load(file)


class FakeReviewBlock:
    def __init__(self) -> None:
        self.content = Mock()
        self.content.inner_text.return_value = "A review"

    def locator(self, selector: str) -> Mock:
        if selector == "a[href*='/app/']":
            app_link = Mock()
            app_link.first.get_attribute.return_value = (
                "https://store.steampowered.com/app/10/Example/"
            )
            return app_link
        if selector == ".bb_more":
            more_button = Mock()
            more_button.count.return_value = 0
            return more_button
        if selector == ".content":
            return self.content
        raise AssertionError(f"Unexpected selector: {selector}")


class FakeReviewBlocks:
    def __init__(self) -> None:
        self.block = FakeReviewBlock()

    def count(self) -> int:
        return 1

    def nth(self, index: int) -> FakeReviewBlock:
        assert index == 0
        return self.block


class FakeReviewPage:
    def __init__(self) -> None:
        self.blocks = FakeReviewBlocks()

    def goto(self, url: str, timeout: int, wait_until: str) -> None:
        assert "recommended/?p=1" in url
        assert timeout == 60000
        assert wait_until == "domcontentloaded"

    def locator(self, selector: str) -> FakeReviewBlocks:
        assert selector == ".review_box"
        return self.blocks

    def __getattr__(self, name: str) -> Any:
        if name == "mouse":
            mouse = Mock()
            mouse.wheel = Mock()
            return mouse
        raise AttributeError(name)

    def wait_for_timeout(self, timeout: int) -> None:
        assert timeout == 500


class FakeReviewContext:
    def __init__(self) -> None:
        self.page = FakeReviewPage()
        self.closed = False

    def new_page(self) -> FakeReviewPage:
        return self.page

    def close(self) -> None:
        self.closed = True


class FakeBrowser:
    def __init__(self) -> None:
        self.context = FakeReviewContext()
        self.closed = False

    def new_context(self) -> FakeReviewContext:
        return self.context

    def close(self) -> None:
        self.closed = True


class FakePlaywright:
    def __init__(self) -> None:
        self.chromium = Mock()
        self.browser = FakeBrowser()
        self.chromium.launch.return_value = self.browser

    def __enter__(self) -> "FakePlaywright":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def test_config_validation_reports_missing_values():
    config = main.Config(
        API_KEY=main.Secret(None),
        STEAM_ID=None,
        STEAM_VANITY=None,
    )

    with pytest.raises(main.ConfigurationError, match="STEAM_API_KEY"):
        config.validate()


def test_mask_secrets_redacts_values(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(main.config, "API_KEY", main.Secret("secret123"))
    monkeypatch.setattr(main.config, "STEAM_ID", "76561198000000000")

    text = "key=secret123 steamid=76561198000000000"
    result = logging_utils.mask_secrets(text)
    assert result is not None

    assert "secret123" not in result
    assert "76561198000000000" not in result


def test_calculate_retry_delay_preserves_retry_after(
    monkeypatch: MonkeyPatch,
) -> None:
    def fixed_uniform(start: float, end: float) -> float:
        return end

    monkeypatch.setattr(
        api.random,
        "uniform",
        fixed_uniform,
    )

    assert main.calculate_retry_delay(10, 60, preserve_delay=True) == 20
    assert main.calculate_retry_delay(-1, 30) == 0


def test_non_retryable_achievement_statuses():
    for status_code in (400, 403):
        response = Response()
        response.status_code = status_code
        error = req_exceptions.HTTPError(response=response)
        assert not main.is_retryable_achievement_error(error)


def test_retryable_achievement_status():
    response = Response()
    response.status_code = 500
    error = req_exceptions.HTTPError(response=response)

    assert main.is_retryable_achievement_error(error)


def test_fetch_games_uses_steam_api_response(monkeypatch: MonkeyPatch) -> None:
    session = Mock()
    response = Mock()
    response.json.return_value = load_fixture("owned_games.json")
    session.get.return_value = response
    monkeypatch.setattr(api, "get_session", lambda: session)
    monkeypatch.setattr(main.config, "API_KEY", main.Secret("test-key"))
    monkeypatch.setattr(main.config, "STEAM_ID", "test-steamid")

    games = main.fetch_games()

    assert games == [{"appid": 10, "name": "Example Game", "playtime_forever": 120}]
    response.raise_for_status.assert_called_once_with()
    session.get.assert_called_once()


def test_fetch_achievements_uses_steam_api_response(
    monkeypatch: MonkeyPatch,
) -> None:
    session = Mock()
    response = Mock()
    response.json.return_value = load_fixture("player_achievements.json")
    session.get.return_value = response
    monkeypatch.setattr(api, "get_session", lambda: session)
    monkeypatch.setattr(main.config, "API_KEY", main.Secret("test-key"))
    monkeypatch.setattr(main.config, "STEAM_ID", "test-steamid")

    result = main.fetch_achievements(10)

    assert result == (10, 2, 1)
    response.raise_for_status.assert_called_once_with()
    session.get.assert_called_once()


def test_owned_games_fixture_matches_contract() -> None:
    assert main.parse_games_response(load_fixture("owned_games.json")) == [
        {"appid": 10, "name": "Example Game", "playtime_forever": 120}
    ]


def test_achievements_fixture_matches_contract() -> None:
    assert main.parse_achievements_response(
        load_fixture("player_achievements.json")
    ) == [
        {"apiname": "EXAMPLE_ONE", "achieved": 1},
        {"apiname": "EXAMPLE_TWO", "achieved": 0},
    ]


@pytest.mark.parametrize(
    ("parser", "payload"),
    [
        (main.parse_games_response, {"response": {"games": "invalid"}}),
        (
            main.parse_achievements_response,
            {"playerstats": {"achievements": "invalid"}},
        ),
    ],
)
def test_api_parsers_reject_invalid_contracts(
    parser: Any,
    payload: object,
) -> None:
    with pytest.raises(ValueError):
        parser(payload)


def test_extract_reviews_uses_browser_context(monkeypatch: MonkeyPatch) -> None:
    playwright = FakePlaywright()
    monkeypatch.setattr(reviews_module, "sync_playwright", lambda: playwright)
    monkeypatch.setattr(main.config, "STEAM_VANITY", "example")
    monkeypatch.setattr(main.config, "MAX_PAGES", 1)

    reviews = main.extract_reviews_playwright()

    assert reviews == {10: "A review"}
    assert playwright.browser.context.closed
    assert playwright.browser.closed


def test_save_outputs_writes_reviews_and_achievements(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(main.config, "REVIEWS_FILE", str(tmp_path / "reviews.csv"))
    monkeypatch.setattr(
        main.config, "ACHIEVEMENTS_FILE", str(tmp_path / "achievements.csv")
    )

    main.save_outputs(
        reviews={10: "A review"},
        games=[{"appid": 10, "name": "Example", "playtime_forever": 120}],
        achievements_map={10: main.AchievementResult(total=10, unlocked=4)},
    )

    with open(main.config.REVIEWS_FILE, encoding="utf-8", newline="") as file:
        reviews = list(csv.DictReader(file))
    with open(main.config.ACHIEVEMENTS_FILE, encoding="utf-8", newline="") as file:
        achievements = list(csv.DictReader(file))

    assert reviews == [{"AppID": "10", "Game Title": "Example", "Review": "A review"}]
    assert achievements[0]["Achievements Total"] == "10"
    assert achievements[0]["Achievements Unlocked"] == "4"
    assert achievements[0]["Completion %"] == "40.0"


def test_save_outputs_handles_zero_achievements(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(main.config, "REVIEWS_FILE", str(tmp_path / "reviews.csv"))
    monkeypatch.setattr(
        main.config, "ACHIEVEMENTS_FILE", str(tmp_path / "achievements.csv")
    )

    main.save_outputs(
        reviews={},
        games=[{"appid": 10, "name": "Example", "playtime_forever": 0}],
        achievements_map={10: main.AchievementResult(total=0, unlocked=0)},
    )

    with open(main.config.ACHIEVEMENTS_FILE, encoding="utf-8", newline="") as file:
        achievements = list(csv.DictReader(file))

    assert achievements[0]["Completion %"] == "0"
