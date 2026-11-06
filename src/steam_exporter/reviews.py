import re

from playwright.sync_api import sync_playwright

from .config import config
from .logging_utils import log


def extract_reviews_playwright() -> dict[int, str]:
    reviews: dict[int, str] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        try:
            page = context.new_page()
            for page_num in range(1, config.MAX_PAGES + 1):
                url = (
                    f"https://steamcommunity.com/id/{config.STEAM_VANITY}/"
                    f"recommended/?p={page_num}"
                )
                log(
                    f"Loading page {page_num}: {url}",
                    source="extract_reviews_playwright",
                )
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
                blocks = page.locator(".review_box")
                previous_count = 0
                for _ in range(5):
                    current_count = blocks.count()
                    if current_count == previous_count and current_count > 0:
                        break
                    previous_count = current_count
                    page.mouse.wheel(0, 20000)
                    page.wait_for_timeout(500)
                count = blocks.count()
                if count == 0:
                    log("No more reviews found.", source="extract_reviews_playwright")
                    break
                for index in range(count):
                    block = blocks.nth(index)
                    app_link = block.locator("a[href*='/app/']").first
                    href = app_link.get_attribute("href")
                    app_match = re.search(r"/app/(\d+)(?:/|$)", href or "")
                    if app_match is None:
                        log(
                            f"Skipped review without a valid AppID on page {page_num}.",
                            source="extract_reviews_playwright",
                        )
                        continue
                    app_id = int(app_match.group(1))
                    more_button = block.locator(".bb_more")
                    if more_button.count() > 0:
                        more_button.click()
                    reviews[app_id] = block.locator(".content").inner_text().strip()
        finally:
            context.close()
            browser.close()
    return reviews
